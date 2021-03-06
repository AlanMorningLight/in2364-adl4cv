"""Config file for Constants and Parameters"""

# DAVIS Paths
ANNOTATIONS_FOLDERS_PATH = "DAVIS_2016/DAVIS/Annotations/480p/"
ANNOTATIONS_AUGMENTED_FOLDERS_PATH = "DAVIS_2016/DAVIS/Annotations_augmented/"
RAW_ANNOTATIONS_PATH = 'pg_datasets/DAVIS_2016/raw/Annotations'

CONTOURS_FOLDERS_PATH = "DAVIS_2016/DAVIS/Contours/"

IMAGES_FOLDERS_PATH = 'DAVIS_2016/DAVIS/JPEGImages/480p/'
IMAGES_AUGMENTED_FOLDERS_PATH = 'DAVIS_2016/DAVIS/JPEGImages_augmented/'

TRANSLATIONS_FOLDERS_PATH = "DAVIS_2016/DAVIS/Translations/"

# PG Dataset Paths
PYTORCH_GEOMETRIC_DAVIS_2016_DATASET_PATH = 'pg_datasets/DAVIS_2016'

# Results Paths
PARENT_MODEL_RESULTS_FOLDERS_PATH = 'OSVOS_PyTorch/models/Results_parent_model'
OSVOS_RESULTS_FOLDERS_PATH = 'OSVOS_PyTorch/models/Results_OSVOS_Tim/'
COMBO_RESULTS_FOLDERS_PATH = 'evaluations/'

PARENT_MODEL_PATH = 'OSVOS_PyTorch/models/parent_epoch-239.pth'

# Sequences
SKIP_SEQUENCES = []

TRAIN_SEQUENCES = ['bear', 'bmx-bumps', 'boat', 'breakdance-flare', 'bus', 
                   'car-turn', 'dance-jump', 'dog-agility', 'drift-turn', 
                   'elephant', 'flamingo', 'hike', 'hockey', 'horsejump-low', 
                   'kite-walk', 'lucia', 'mallard-fly', 'mallard-water', 
                   'motocross-bumps', 'motorbike', 'paragliding', 'rhino', 
                   'rollerblade', 'scooter-gray', 'soccerball', 'stroller',
                   'surf', 'swing', 'tennis', 'train']

VAL_SEQUENCES = ['blackswan', 'bmx-trees', 'breakdance', 'camel', 'car-roundabout',
                 'car-shadow', 'cows', 'dance-twirl', 'dog', 'drift-chicane', 
                 'drift-straight', 'goat', 'horsejump-high', 'kite-surf', 'libby', 
                 'motocross-jump', 'paragliding-launch', 'parkour', 'scooter-black', 
                 'soapbox']

DEBUG = 1000

# Data Augmentation
AUGMENTATION_COUNT = 0
MEANVAL = (104.00699, 116.66877, 122.67892)

# Contour and Translation Creation
CLOSING_KERNEL_SIZE = 25

# Dataset Creation
LAYER = 30
K = 32
NUM_TRAIN_SEQUENCES = 30
NUM_VAL_SEQUENCES = 20

# Training parameters
BATCH_SIZE = 4
LEARNING_RATE = 1e-5
WEIGHT_DECAY = 0.0
NUM_EPOCHS = 20

# Testing
USE_PARENT_MODEL_RESULTS = False
BEST_MODEL = 'pg_models/2019-08-02_12:52:05_0_30_32_30_20_1e-05_0.0_best_model.pth'
