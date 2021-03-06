import boto3
import os
import logging
import datetime

# Set parameters
bucketName = 'hcp-openaccess'
prefix = 'HCP_1200'
outputPath =  'G:\\'

theTime = datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
os.makedirs(theTime)

logger = logging.getLogger('script')
formatter = logging.Formatter('%(asctime)s[line:%(lineno)d] - %(levelname)s: %(message)s')
logger.setLevel(level = logging.DEBUG)
logger.propagate = False

file_handler = logging.FileHandler('./{}/INFO.log'.format(theTime))
file_handler.setLevel(level = logging.INFO)
file_handler.setFormatter(formatter)

warning_handler = logging.FileHandler('./{}/WARNING.log'.format(theTime))
warning_handler.setLevel(level = logging.WARNING)
warning_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(warning_handler)
logger.addHandler(stream_handler)



def download_subject(bucket, subject_number, output_path):
    # Get the target file list
    keyList = bucket.objects.filter(Prefix = prefix + '/{}/MNINonLinear/Results/tfMRI'.format(subject_number))
    keyList = [key.key for key in keyList]
    keyList = [x for x in keyList if '_LR.nii.gz' in x or '_RL.nii.gz' in x or 'EVs' in x]
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        
    totalNumber = len(keyList)
    trycnt = 0
    
    
    
    tempKeys = [x for x in keyList if '_LR.nii.gz' in x or '_RL.nii.gz' in x]
    if len(tempKeys) != 14:
        logger.warning('%s: just havs %d keys, please check again!', subject_number, totalNumber)
    
    logger.info('%s: Begin to download %d keys', subject_number, totalNumber)
    for idx, tarPath in enumerate(keyList):
        downloadPath = os.path.join(output_path, tarPath)
        downloadDir = os.path.dirname(downloadPath)
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)
        while trycnt < 10:
            try:
                if not os.path.exists(downloadPath):
                    bucket.download_file(tarPath, downloadPath)
#                    logger.info('%s: %s downloaded!  %d/%d', subject_number, tarPath.split('/')[-1], idx + 1, totalNumber)
#                else:
#                    logger.info('%s: %s already exists!  %d/%d', subject_number, tarPath.split('/')[-1], idx + 1, totalNumber)
                if (idx + 1)%(totalNumber//4) == 0:
                    logger.info('%s: %.2f%% downloaded!', subject_number, (float((idx + 1)/totalNumber) * 100))
                if trycnt > 0:
                    ('%s: %s downloded!  %d/%d', subject_number, tarPath.split('/')[-1], idx + 1, totalNumber)
                trycnt = 0
                break
            except Exception as exc:
                trycnt += 1
                logger.error('%s: %s error!  %d/%d (%s tries)', subject_number, tarPath.split('/')[-1], idx + 1, totalNumber, trycnt)
                logger.error('{}'.format(str(exc)))
        if trycnt == 10:
            logger.error('%s: %s did not download!', subject_number, tarPath.split('/')[-1])
            
    logger.info('%s completed!', subject_number)
    
    with open('downloaded.txt', 'a') as fa:
        fa.write(subject_number + '\n')

def main():
    logger.info('Loading...')
    # Init variable
    boto3.setup_default_session()
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketName)
    logger.info('Bucket built!')
    
    
    downloadedList = []
    
    if not os.path.exists('./downloaded.txt'):
        fw = open('./downloaded.txt', 'w')
        fw.close()
        
    with open('./downloaded.txt', 'r') as fr:
        for subject_number in fr.readlines():
            subject_number = subject_number.strip()
            downloadedList.append(subject_number)
    
    downloaded = len(downloadedList)
    
    
    with open('./subjects.txt', 'r') as fr:
        for subject_number in fr.readlines():
            subject_number = subject_number.strip()
            if subject_number in downloadedList:
                logger.warning('%s already downloaded', subject_number)
                continue
            download_subject(bucket, subject_number, outputPath)
            downloaded += 1
            logger.info('%s subjects have been downloaded!', downloaded)
            

if __name__ == '__main__':
    main()
