import logging
import redis
import json
import datetime
import cloudlanguagetools.servicemanager
import cloudlanguagetools.constants
import posthog

from .quotas import get_usage_record
from ..fields.vocabai_models import VocabAiLanguageData

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

manager = cloudlanguagetools.servicemanager.ServiceManager() 
manager.configure_default()

User = get_user_model()

def reload_manager():
    global manager
    manager = cloudlanguagetools.servicemanager.ServiceManager() 
    manager.configure_default()

def get_servicemanager():
    return manager

def update_language_data():
    logger.info('retrieving language data')
    language_list = manager.get_language_list()
    language_data = manager.get_language_data_json_v2()

    language_data_records = VocabAiLanguageData.objects.all()
    
    if len(language_data_records) == 1:
        language_data_record = language_data_records[0]
    else:
        # create new record
        language_data_record = VocabAiLanguageData()
    
    # update the record
    language_data_record.language_list = language_list
    language_data_record.free_transformation_options = language_data['free']
    language_data_record.premium_transformation_options = language_data['premium']

    # update database
    language_data_record.save()

    logger.info('saved language data')
        
def get_language_data_record():
    language_data_records = VocabAiLanguageData.objects.all()
    if len(language_data_records) != 1:
        raise Exception(f'could not find language data record')
    return language_data_records[0]

def get_language_list():
    return get_language_data_record().language_list

def get_translation_options():
    return get_language_data_record().premium_transformation_options['translation_options']

def get_transliteration_options():
    return get_language_data_record().premium_transformation_options['transliteration_options']

def get_dictionary_lookup_options():
    return get_language_data_record().premium_transformation_options['dictionary_lookup_options']

def get_translation_services_source_target_language(source_language, target_language):
    translation_options = get_translation_options()
    source_language_options = [x for x in translation_options if x['language_code'] == source_language]
    target_language_options = [x for x in translation_options if x['language_code'] == target_language]
    source_services = [x['service'] for x in source_language_options]
    target_services = [x['service'] for x in target_language_options]
    service_list = list(set(source_services).intersection(target_services))
    return service_list

def report_posthog_usage(user_id, request_type: cloudlanguagetools.constants.RequestType, text: str, service: str):
    try:
        platform = 'vocab-words'
        # lookup user by user_id
        user = User.objects.get(id=user_id)
        posthog.capture(user.email, 'clt_usage_v1', {
            'clt_platform': platform,
            'clt_request_type': request_type.name,
            'clt_client': platform,
            'clt_service': service,
            'clt_text': text,
            'clt_account_type': platform,
        })
    except Exception as e:
        logger.error(f'error reporting posthog usage: {e}')


def get_translation(text, source_language, target_language, service, usage_user_id):
    request_type: cloudlanguagetools.constants.RequestType = cloudlanguagetools.constants.RequestType.translation
    translation_options = get_translation_options()
    source_language_options = [x for x in translation_options if x['language_code'] == source_language and x['service'] == service]
    target_language_options = [x for x in translation_options if x['language_code'] == target_language and x['service'] == service]
    source_language_key = source_language_options[0]['language_id']
    target_language_key = target_language_options[0]['language_id']

    usage_record = get_usage_record(usage_user_id)
    character_cost = manager.service_cost(text, service, request_type)    
    logger.debug(f'character_cost: {character_cost}, service: {service}')
    usage_record.check_quota_available(character_cost)

    translated_text = manager.get_translation(text, service, source_language_key, target_language_key)


    usage_record.update_usage(character_cost)
    report_posthog_usage(usage_user_id, request_type, text, service)

    return translated_text


def get_transliteration(text, transliteration_id, usage_user_id):
    request_type: cloudlanguagetools.constants.RequestType = cloudlanguagetools.constants.RequestType.transliteration
    transliteration_options = get_transliteration_options()
    transliteration_option = [x for x in transliteration_options if x['transliteration_id'] == transliteration_id]
    service = transliteration_option[0]['service']
    transliteration_key = transliteration_option[0]['transliteration_key']

    usage_record = get_usage_record(usage_user_id)
    character_cost = manager.service_cost(text, service, request_type)
    usage_record.check_quota_available(character_cost)

    translated_text = manager.get_transliteration(text, service, transliteration_key)


    usage_record.update_usage(character_cost)
    report_posthog_usage(usage_user_id, request_type, text, service)

    return translated_text    


def get_dictionary_lookup(text, lookup_id, usage_user_id):
    request_type: cloudlanguagetools.constants.RequestType = cloudlanguagetools.constants.RequestType.dictionary
    dictionary_lookup_options = get_dictionary_lookup_options()
    lookup_option = [x for x in dictionary_lookup_options if x['lookup_id'] == lookup_id]
    service = lookup_option[0]['service']
    lookup_key = lookup_option[0]['lookup_key']

    usage_record = get_usage_record(usage_user_id)
    character_cost = manager.service_cost(text, service, request_type)
    usage_record.check_quota_available(character_cost)

    try:
        lookup_result = manager.get_dictionary_lookup(text, service, lookup_key)

        usage_record.update_usage(character_cost)        
        report_posthog_usage(usage_user_id, request_type, text, service)

        if isinstance(lookup_result, list):
            return ' / '.join(lookup_result)
        elif isinstance(lookup_result, dict):
            result_list = []
            for key, value in lookup_result.items():
                result_list.append(key + ': ' + ' / '.join(value))
            return ', '.join(result_list)
        else:
            return str(lookup_result)
    except cloudlanguagetools.errors.NotFoundError:
        return None


def get_pinyin(text, tone_numbers, spaces, usage_user_id, corrections=[]):
    report_posthog_usage(usage_user_id, cloudlanguagetools.constants.RequestType.transliteration, text, cloudlanguagetools.constants.Service.MandarinCantonese)
    result = manager.get_pinyin(text, tone_numbers, spaces, corrections=corrections)
    return enhance_chinese_romanization_result(result)

def get_jyutping(text, tone_numbers, spaces, usage_user_id, corrections=[]):
    report_posthog_usage(usage_user_id, cloudlanguagetools.constants.RequestType.transliteration, text, cloudlanguagetools.constants.Service.MandarinCantonese)
    result =  manager.get_jyutping(text, tone_numbers, spaces, corrections=corrections)
    return enhance_chinese_romanization_result(result)

def enhance_chinese_romanization_result(result):
    result['format_revision'] = 3
    result['rendered_solution'] = ' '.join(word[0] for word in result['solutions'])
    result['solution_overrides'] = [0] * len(result['solutions'])
    return result
 
def update_rendered_solution(romanization):
    if romanization != None and romanization != {}:
        rendered_solution_override = romanization.get('rendered_solution_override', None)
        if rendered_solution_override:
            rendered_solution = rendered_solution_override
        else:
            rendered_solution = ' '.join(word[word_index] for word, word_index in zip(romanization['solutions'], romanization['solution_overrides']))
        romanization['rendered_solution'] = rendered_solution
    return romanization