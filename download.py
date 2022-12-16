# use this scrip to download images from urls in the GBIF darwin core zip file
# run as `python3 download.py <path to zip file>`

import json
import os
import shutil
import urllib.request
import zipfile
import pandas as pd
from tqdm import tqdm
import sys

try:
    path_to_zip = str(sys.argv[1])
except:
    print('ERROR: No zip file specified.')
    quit()

extracted_folder = path_to_zip.split('/')[-1][:-4] # get zip file name 

# extract files from GBIF darwin zip
try:
    with zipfile.ZipFile(path_to_zip) as z:
        z.extractall(extracted_folder)
        print("Files extracted.")
except:
    print('Error: \'{}\' does not exist.'.format(path_to_zip))
    quit()

# get species info
occurrence = pd.read_csv(extracted_folder + '/occurrence.txt', sep='\t')

# check if only one species in dataset
if len(set(occurrence['taxonKey'])) > 1:
    print('ERROR: More than one species in dataset.')
    print(set(occurrence['scientificName']))

    # confirmation for multiple species - in case of synomymns 
    confirmation = input("Continue anyway? (y/n)")
    if confirmation == 'y':
        taxonKey = str(occurrence['taxonKey'][0])
        species = str(occurrence['species'][0]).lower().replace(" ", "_")
    elif confirmation == 'n':
        # remove extrated files and quit
        shutil.rmtree(extracted_folder) 
        quit()
    else:
        print("The only acceptable inputs are 'y' or 'n', try again.")
        shutil.rmtree(extracted_folder) 
        quit()
else:
    taxonKey = str(occurrence['taxonKey'][0])
    species = str(occurrence['species'][0]).lower().replace(" ", "_")

# path to temp downloads folder
download_folder = './' + species + '/'
download_folder_imgs = download_folder + 'imgs/'

# create the downloads folder if it doesn't exist yet
if not os.path.exists(download_folder):
    os.makedirs(download_folder)
    os.makedirs(download_folder_imgs)
    print('Folder \'{}\' created.'.format(species))
else:
    print('Folder \'{}\' already exists.'.format(species))

# get urls
multimedia = pd.read_csv(extracted_folder + '/multimedia.txt', sep='\t')
urls = multimedia['identifier']

# count how many files to download
img_count = urls.shape[0]
# download urls 
print('{} files will be downloaded'.format(img_count))

# saving metadata about the dataset
meta = {
    'taxonKey' : taxonKey,
    'species' : species,
    'multimedia_count' : img_count,
    'multimedia_urls' : list(multimedia['identifier'])
}

gbif_json = 'gbif-metadata.json'
with open(gbif_json , "w") as outfile:
    json.dump(meta, outfile, indent=4)

# download all files
for i in tqdm(range(img_count)):
    url = urls[i]
    file_name = urls[i].split('/')[-2] # photo id in iNaturalist
    ext = os.path.splitext(url)[1]
    downloaded_file_name = species + '-' + file_name + ext
    save_to = download_folder + 'imgs/' + downloaded_file_name
    if not os.path.isfile(save_to): # check if file already exists, if not try to download
        try:
            urllib.request.urlretrieve(url, save_to)
        except:
            print('ERROR: did not download [{}]: {}'.format(i, url))

# make a new count for multimedia for unique urls and only actually downloaded urls
# also need to create new list of urls as some might not be downloaded due to errors

# clean up
shutil.move(gbif_json, download_folder)      # move json
# shutil.move(path_to_zip, download_folder)    # move zip file
shutil.rmtree(extracted_folder)              # delete unziped data and contents

print('Done. All files moved to \'{}\''.format(download_folder))