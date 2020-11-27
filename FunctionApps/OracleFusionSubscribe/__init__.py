from datetime import datetime
import io
import json
import logging
import os
from tempfile import TemporaryDirectory
import uuid
from zipfile import ZipFile

import azure.functions as func

from utility.api.lake import DataLakeHook
from utility.api.soap import OracleFusionHook

lake_client = DataLakeHook(
    lake_url=os.environ['LAKE_URL'], 
    lake_key=os.environ['LAKE_KEY'])
erp_client = OracleFusionHook(
    user=os.environ['FUSION_USER'], 
    password=os.environ['FUSION_USER_PWD'], 
    soap_uri=os.environ['SOAP_URI'], 
    erp_uri=os.environ['ERP_URI'])


def main(event: func.EventGridEvent,
         outputBlob: func.Out[func.InputStream]):
        
    data = event.get_json()
    logging.info(f"Type: {type(data)}, {data.get('file_name_prefix', None)}")

    result = json.dumps({
        'id': event.id,
        'data': data,
        'data_type': str(type(data)),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    }, indent=4)

    logging.info(f'Saving payload as blob: {result}')

    outputBlob.set(result)

    logging.info(f'Searching for content in Oracle')

    file_name_prefix = data.get('file_name_prefix', 'MANIFEST_DATA_41')
    lake_container = data.get('lake_container', 'event-grid-subscribe')
    lake_path = data.get('lake_path', 'output')

    search_query = f"""
    dOriginalName <starts> `{file_name_prefix}`
    <AND> dSecurityGroup <starts> `OBIAImport`
    """.strip()

    logging.info(f"Searching files for '{file_name_prefix}'")

    results_df = erp_client.get_search_results(search_query)

    if results_df.shape[0] > 0:
        logging.info(f"Found {results_df.shape[0]} documents")
    else:
        raise Exception(f"No documents found")

    for r in results_df.itertuples(index=False):
        logging.info(f"Downloading {r.dOriginalName} to {lake_path}")

        docs_df, content = erp_client.get_content(r.dID)

        for attach in content:

            logging.info(f"Uploading to lake")

            content_type = docs_df.loc[
                docs_df.dOriginalName == attach['href'],
                'dFormat'].iloc[0]

            if content_type == 'application/zip':
                with ZipFile(io.BytesIO(attach['Contents'])) as z:  # ?
                    for member in z.infolist():
                        file_name = f"{uuid.uuid4()}-{member.filename}"
                        data = z.open(name=member.filename)

                        lake_client.upload_data(lake_container=lake_container,
                                                lake_dir=lake_path,
                                                file_name=file_name,
                                                data=data.read())
            else:
                file_name = f"{uuid.uuid4()}-{attach['href']}"
                
                lake_client.upload_data(lake_container=lake_container,
                                        lake_dir=lake_path,
                                        file_name=file_name,
                                        data=attach['Contents'])

        logging.info(f"Downloaded {docs_df.shape[0]} documents")

    logging.info(f'Python EventGrid trigger processed an event: {result}')
