"""Functions for creating a torch_geometric.data object that is used to create a custom 
   PyTorch Geometric custom dataset class for the DAVIS 2016 dataset."""

import numpy as np
from scipy.misc import imread, imsave, imresize

import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.nn import knn_graph
from torch_geometric.utils import to_undirected

import OSVOS_PyTorch.networks.vgg_osvos as vo


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def create_osvos_model(model_path, layer):
    """Creates OSVOS model from which feature vectors can be extracted.
    
    1st CONV block 1-4 --> Shape: [1, 64, 480, 854] --> Receptive field: 5
    2nd CONV block 5-9 --> Shape: [1, 128, 240, 427] --> Receptive field: 5 * 2(pooling) + 4 = 14
    3rd CONV block 10-16 --> Shape: [1, 256, 120, 214] --> Receptive field: 14 * 2 + 6 = 34
    4th CONV block 17-23 --> Shape: [1, 512, 60, 107] --> Receptive field: 34 * 2 + 6 = 74
    5th CONV block 24-30 --> Shape: [1, 512, 30, 54] --> Receptive field: 74 * 2 + 6 = 154

    Parameters
    ----------
    model_path : str
        Path to trained OSVOS model
    layer : int
        Layer from which to extract OSVOS feature vector (1, 4, 9, 16 are useful values)

    Returns
    -------
    new_model : torch.nn.Sequential
        OSVOS model from which feature vectors can be extracted
    """

    # Load original OSVOS model
    model = vo.OSVOS(pretrained=0)
    model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))
    model.eval()            

    # Load only stages of OSVOS architecture
    children = []
    for num, stage in enumerate(model.stages):
        if type(stage) == torch.nn.modules.container.Sequential:
            for child in stage.children():
                children.append(child)

    # Create new model at given layer
    new_model = nn.Sequential(*children[:layer])
    new_model = new_model.double()
    new_model.eval()

    gpu_id = 0
    device = torch.device("cuda:"+str(gpu_id) if torch.cuda.is_available() else "cpu")
    new_model.to(device)

    return new_model

def get_OSVOS_feature_vectors(contour, img, osvos_model):
    """Returns OSVOS feature vector for each contour point.

    Parameters
    ----------
    contour : ndarray of shape (num_contour_points, 2)
        Array containing contour points
    img : ndarray
        OSVOS image from which contour points were extracted
    osvos_model : torch.nn.Sequential
        OSVOS model from which feature vectors can be extracted

    Returns
    -------
    feature_vectors : torch tensor
        Tensor containing the feature vectors for each contour point
    """
    
    gpu_id = 0
    img = img.to(device)
    
    with torch.no_grad():
        feature_vector = osvos_model(img)

    # Extract vector out of output tensor depending on keypoint location
    # Compute receptive fields for every feature vector
    # --> Select feature vector which receptive field center is closest to key point
    _, _, height_img, width_img = img.cpu().numpy().shape
    _, _, height_fv, width_fv = feature_vector.detach().cpu().numpy().shape
    
    feature_vectors = []
    for contour_point in contour:
        x_cp, y_cp = contour_point
        
        # If contourpoint in image return feature vector else zero vector
        if (x_cp <= width_img) and (y_cp <= height_img):
            x_fv, y_fv = (int(float(x_cp) * width_fv / width_img) - 2, 
                          int(float(y_cp) * height_fv / height_img) - 2)
            feature_vectors.append(feature_vector[: ,: , y_fv, x_fv].cpu().numpy())
        else:
            feature_vectors.append(np.zeros(feature_vector.shape[1]))
        
    feature_vectors = np.squeeze(np.array(feature_vectors))
    
    return torch.from_numpy(feature_vectors)


def get_edge_attribute(contour, edge_index):
    """Returns an edge feature matrix of shape (num_edges, num_edge_features)
       containing the inverse distances between the node each edge connects.

    Parameters
    ----------
    contour : ndarray of shape (num_contour_points, 2)
        Array containing contour points
    edge_index : torch tensor
        Graph connectivity in COO format of shape (2, num_edges) and type torch.long

    Returns
    -------
    edge_attr : torch tensor
        Tensor containing the edge feature matrix of shape (num_edges, num_edge_features)
    """
    
    edge_index = edge_index.numpy()
    edge_index = edge_index.T
    
    edge_attr = []
    for edge in edge_index:
        contour_point_0 = contour[edge[0]] 
        contour_point_1 = contour[edge[1]]
        dist = np.linalg.norm(contour_point_0-contour_point_1)
        inverse_dist = 1 / (1 + dist)
        edge_attr.append([inverse_dist])
    
    edge_attr = np.array(edge_attr).astype(np.float64)
    edge_attr = np.squeeze(edge_attr)
    
    return torch.from_numpy(edge_attr)


def create_data(contour, translation, img_path_0, img_path_1, osvos_model, k):
    """Returns a torch_geometric.data object.
    
    The data object consists of:
    * x: Node feature matrix of shape [num_nodes, num_node_features]. The feature 
         of each node are the concatenated OSVOS feature vectors of the current 
         and the next frame.
    * edge_index: Graph connectivity in COO format of shape (2, num_edges) and type torch.long
                  Each node should be connected to its K nearest neighbours
    * edge_attr: Edge feature matrix with shape [num_edges, num_edge_features]
                 The feature of each edge is the inverse distance between the two nodes it connects
    * y, optianl: The target of each node is the displacement of the node between the current 
                  and the next frame

    Parameters
    ----------
    contour : ndarray 
        Array of shape (num_contour_points, 2) containing contour points
    translation : ndarray of shape (num_contour_points, 2)
        Array of shape (num_contour_points, 2) containing translations from current to next contour point
    img_path_0 : str
        Path to current image
    img_path_0 : str
        Path to next image
    osvos_model : torch.nn.Sequential
        OSVOS model from which feature vectors can be extracted
    k : int
        Number of neighbours to compute KNN graph of contour points

    Returns
    -------
    data : torch_geometric.data
        Data object containing consisting of x, edge_index, edge_attr, and y
    """
    
    contour = torch.from_numpy(contour)
    
    img_0 = np.moveaxis(imread(img_path_0), 2, 0).astype(np.float64)
    img_0 = np.expand_dims(img_0, axis=0)
    img_0 = torch.from_numpy(img_0)    
    
    img_1 = np.moveaxis(imread(img_path_1), 2, 0).astype(np.float64)
    img_1 = np.expand_dims(img_1, axis=0)
    img_1 = torch.from_numpy(img_1)
    
    # x: Node feature matrix
    x_1 = get_OSVOS_feature_vectors(contour, img_0, osvos_model)
    x_2 = get_OSVOS_feature_vectors(contour, img_1, osvos_model)
    x = torch.cat((x_1, x_2), 1)
    
    # edge_index: Graph connectivity in COO format 
    edge_index = knn_graph(contour, k)
    edge_index = to_undirected(edge_index)

    # edge_attr: Edge feature matrix 
    edge_attr = get_edge_attribute(contour, edge_index)
    
    # Create data object
    if translation is None:
        data = Data(x=x, edge_index=edge_index, 
                    edge_attr=edge_attr, contour=contour)
    else:
        # The target of each node is the displacement of the node between the current and the next frame
        y = torch.from_numpy(translation.astype(np.float64))
        data = Data(x=x, edge_index=edge_index, 
                    edge_attr=edge_attr, y=y, contour=contour)

    return data