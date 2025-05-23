import joblib

# Load the model using joblib  
model_file = './local_model/kmeans_github_model.h5'

# Load the model (if it's a Scikit-learn model)
kmeans_model = joblib.load(model_file)

# Load the pre-trained MinMaxScaler  
scaler_file = './local_model/standard_scaler.pkl'  
scaler = joblib.load(scaler_file)


def assign_marks(prediction, allocatedMarks):
    """
    Assign marks based on the prediction value.
    """
    cluster_priority = [3, 2, 1, 4, 0]

    if prediction not in cluster_priority:
        raise ValueError(f"Invalid prediction: {prediction}. Must be one of {cluster_priority}.")

    # # Determine the priority rank (0-based index)
    rank = cluster_priority.index(prediction)
    
    print(f"Rank: {rank}")

    # # Calculate the marks
    marks_ratio =  (len(cluster_priority) - rank) / len(cluster_priority)
    print(f"Marks Ratio: {marks_ratio}")

    allocatedMarks = float(allocatedMarks)
   
    print(f"Allocated Marks: {allocatedMarks}")
    
    return allocatedMarks * marks_ratio