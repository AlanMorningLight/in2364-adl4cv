from distutils.dir_util import copy_tree
import numpy as np
import os

import torch
import torch.nn as nn
from torch_geometric.data import Data, Dataset
from torch_geometric.nn import knn_graph
from torch_geometric.utils import to_undirected

from pg_datasets.create_data import create_data
import OSVOS_PyTorch.networks.vgg_osvos as vo


class DAVIS2016(Dataset):
    def __init__(self, root, 
                 contours_folders_path, images_folders_path, translations_folders_path, 
                 layer, k, 
                 skip_sequences, train_sequences, val_sequences,
                 train=True, transform=None, pre_transform=None):
        # Paths    
        self.contours_folders_path = contours_folders_path
        self.images_folders_path = images_folders_path
        self.translations_folders_path = translations_folders_path
        
        # Hyperparameters
        self.layer = layer
        self.k = k
        
        # Sequences
        self.skip_sequences = skip_sequences
        self.train_sequences = train_sequences
        self.val_sequences = val_sequences
        
        self.train = train
        
        super(DAVIS2016, self).__init__(root, transform, pre_transform)
        
    @property
    def raw_file_names(self):
        raw_file_names = ['Contours', 'JPEGImages', 'Translations']
        return raw_file_names

    @property
    def processed_file_names(self):
        
        processed_file_names = []
        
        # Get path to Translations
        raw_path_translations = self.raw_paths[2]
        
        # Get list of sequences
        sequences = os.listdir(raw_path_translations)
        sequences.sort()
        
        # Iterate through sequences 
        for i, sequence in enumerate(sequences):
            
            #if i > 2: break
            
            # Skip sequence if needed
            if (sequence in self.skip_sequences): continue
                
            # Train or val dataset
            if self.train:
                if (sequence in self.val_sequences): continue
            else:
                if (sequence in self.train_sequences): continue
                
                
            # Get path to Translations folder
            translations_folder_path = os.path.join(raw_path_translations, sequence)
            
            # Get list of frames
            frames = os.listdir(translations_folder_path)
            frames.sort()
            
            # Iterate through frames
            for j, frame in enumerate(frames):
                
                #if j > 2: break
                    
                processed_file_names.append('{}_{}.pt'.format(sequence, frame[:5]))
        
        return processed_file_names
    
    def __len__(self):
        return len(self.processed_file_names)
        
    def  download(self):
         
        print('Downloading...')
         
        # Copy Contours folder to raw_dir
        raw_dir_contours = os.path.join(self.raw_dir, 'Contours')
        copy_tree(self.contours_folders_path, raw_dir_contours)
        
        # Copy JPEGImages folder to raw_dir
        raw_dir_images = os.path.join(self.raw_dir, 'JPEGImages')
        copy_tree(self.images_folders_path, raw_dir_images)
        
        # Copy Translations folder to raw_dir
        raw_dir_translations = os.path.join(self.raw_dir, 'Translations')
        copy_tree(self.translations_folders_path, raw_dir_translations)
    
    def _create_osvos_model(self, model_path, layer):
        
        model = vo.OSVOS(pretrained=0)
        model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))
        model.eval()            
            
        children = []
        for num, stage in enumerate(model.stages):
            if type(stage) == torch.nn.modules.container.Sequential:
                for child in stage.children():
                    children.append(child)

        new_model = nn.Sequential(*children[:layer])
        new_model = new_model.double()
        new_model.eval()
            
        gpu_id = 0
        device = torch.device("cuda:"+str(gpu_id) if torch.cuda.is_available() else "cpu")
        new_model.to(device)
        
        return new_model
        
    def process(self):
        # Get paths to Contours, Images, and Translations
        raw_path_contours, raw_path_images, raw_path_translations = self.raw_paths
        
        # Get list of sequences
        sequences = os.listdir(raw_path_contours)
        sequences.sort()
        
        # Iterate through sequences 
        for i, sequence in enumerate(sequences):
            
            #if i > 2: break
            
            # Skip sequence if needed
            if (sequence in self.skip_sequences): continue
                    
            # Train or val dataset
            if self.train:
                if (sequence in self.val_sequences): continue
            else:
                if (sequence in self.train_sequences): continue
            
            print('#{}: {}'.format(i, sequence))
            
            # Get paths to current sequence in Contours and Translations folders
            contours_folder_path = os.path.join(raw_path_contours, sequence)
            images_folder_path = os.path.join(raw_path_images, sequence)
            translations_folder_path = os.path.join(raw_path_translations, sequence)
            
            # Start train_online for this sequence 
            model_path = '/home/christoph/in2364-adl4cv/OSVOS_PyTorch/models/' + str(sequence) + '_epoch-24.pth'
            print('Start online training...')
            
            if not os.path.exists(model_path):
                os.environ['SEQ_NAME'] = str(sequence)
                # TODO: remove absolute path
                os.system('python /home/christoph/in2364-adl4cv/OSVOS_PyTorch/train_online.py')
            
            print('Finished online training...')
            
            # Create OSVOS model for feature vector extraction
            print('Create new OSVOS model...')
            new_model = self._create_osvos_model(model_path, self.layer)
            
            # Get list of translations (one for each frame in the sequence)
            frames = os.listdir(contours_folder_path)
            frames.sort()
            
            # Iterate through frames
            for j, frame in enumerate(frames[:-1]):
                
                #if j > 2: break
                    
                print('#{}: {}'.format(j, frame))
                
                # Load corresponding contour
                contour_path = os.path.join(contours_folder_path, frame)
                contour = np.load(contour_path)
                
                # Load corresponding sequence
                translation_path = os.path.join(translations_folder_path, frame)
                translation = np.load(translation_path)
                
                # Get image path
                image_path = os.path.join(images_folder_path, frames[j+1][:5] + '.jpg')
                
                # Get data and append it to corresponding data_list
                data = create_data(contour, translation, image_path, new_model, self.k)

                if self.pre_filter is not None and not self.pre_filter(data):
                    continue

                if self.pre_transform is not None:
                    data = self.pre_transform(data)
                
                torch.save(data, os.path.join(self.processed_dir, '{}_{}.pt'.format(sequence, frame[:5])))

    def get(self, idx):
        data = torch.load(os.path.join(self.processed_dir, self.processed_file_names[idx]))
        return data