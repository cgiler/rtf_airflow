import json
import os
from datetime import datetime

from essence.analytics.platform import securedcredentials as secure_creds

from RTF.rtf_utils.dfa_utils import (CampaignManagerReport, clean_dcm_file,
                                 get_dfa_report)
from RTF.rtf_utils.gcp_utils import BigQuery, CloudStorage

bucket_name = 'rtf_staging'
PROJECT_ID='essence-analytics-dwh'
service_account_email='131786951123-compute@developer.gserviceaccount.com'



def dfa_report_extract(report_id,**context):
    start_date = context['ds']
    end_date = context['ds']
    
    credentialsFromVault=secure_creds.getCredentialsFromEssenceVault(service_account_email)
    
    local_filename = get_dfa_report(credentialsFromVault,
                                report_id,
                                start_date,
                                end_date)
    print("Cleaning File")
    clean_dcm_file(local_filename)
    
    print("Auth GCS")
    gcs = CloudStorage(credentialsFromVault)
    folder = "brand_reporting/"
    destination_blob_name = folder + local_filename

    print("Upload File")
    
    gcs.upload_blob(bucket_name, destination_blob_name, local_filename, mode='filename')
    
    stored_blob = gcs.get_blob(bucket_name,destination_blob_name)
          
    print("Clean Up Local")
    os.remove(local_filename)
    
    return "gs://" + stored_blob.bucket.name + "/" + stored_blob.name


def dfa_report_load(pull_task_id,dataset_table,schema=None,**context):
    file_uri = context['ti'].xcom_pull(task_ids=pull_task_id)
    
    print("Get Creds from Vault")
    
    credentialsFromVault=secure_creds.getCredentialsFromEssenceVault(service_account_email)
    
    dataset_id = dataset_table.split(".")[0]
    dest_table = dataset_table.split(".")[1]
    
    print("Auth BQ")
    bq = BigQuery(credentialsFromVault)
    
    print("Load to BQ")
    bq.load_from_gcs(dataset_id,file_uri,dest_table,mode='Append')