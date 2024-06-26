import random

from scipy.io import loadmat
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.nn import init
import torch.nn as nn
import torch.optim as optim
from sklearn import preprocessing
from sklearn.model_selection import KFold
import torch.nn.functional as F
import torch.utils.data as Data
from sklearn.metrics import accuracy_score, recall_score, f1_score, precision_score, precision_recall_fscore_support
import time
import os
from torch.utils.data import DataLoader, Subset, TensorDataset
import warnings
# 忽略特定类型的警告
warnings.filterwarnings("ignore", message="Precision is ill-defined and being set to 0.0 in labels with no predicted samples.")

print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
os.environ["CUDA_VISIBLE_DEVICES"] = '3'


def setup_seed(seed): # Set random seed
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # if you are using multi-GPU.
    np.random.seed(seed)  # Numpy module.
    random.seed(seed)  # Python random module.
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def weigth_init(m):  ## model parameter intialization
    if isinstance(m, nn.Conv1d):
        init.xavier_uniform_(m.weight.data)
        if m.bias is not None:
            init.constant_(m.bias.data, 0.3)
    elif isinstance(m, nn.BatchNorm2d):
        m.weight.data.fill_(1)
        m.bias.data.zero_()
    elif isinstance(m, nn.BatchNorm1d):
        m.weight.data.fill_(1)
        m.bias.data.zero_()
    elif isinstance(m, nn.Linear):
        m.weight.data.normal_(0,0.03)
#        torch.nn.init.kaiming_normal_(m.weight.data,a=0,mode='fan_in',nonlinearity='relu')
        m.bias.data.zero_()


def load_dataset(trial, batch_size, num_folds):
    path1 = "D:\python\pythonProject3\BCI_learn\\11111\weight_data"
    path2 = "D:\python\pythonProject3\BCI_learn\\11111\label"
    feature = loadmat("{}\\{}.mat".format(path1, trial))["Value"]
    label = loadmat("{}\\{}.mat".format(path2, trial))["label"].squeeze()
    feature = np.moveaxis(feature, 0, 2)
    feature= feature/30
    feature_tensor = torch.tensor(feature, dtype=torch.float32)
    label_tensor = torch.tensor(label, dtype=torch.long)
    dataset = TensorDataset(feature_tensor, label_tensor)

    test_size = int(0.2 * len(dataset))
    train_size = len(dataset) - test_size
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    kf = KFold(n_splits=num_folds, shuffle=True,random_state=42)

    train_loaders = []
    valid_loaders = []

    for train_idx, valid_idx in kf.split(train_dataset):
        train_subset = Subset(train_dataset, train_idx)
        valid_subset = Subset(train_dataset, valid_idx)

        train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True)
        valid_loader = DataLoader(valid_subset, batch_size=batch_size, shuffle=False)

        train_loaders.append(train_loader)
        valid_loaders.append(valid_loader)

    return train_loaders, valid_loaders, test_loader



class ResidualBlock(nn.Module):
    def __init__(self, inchannel, outchannel, stride=1, shortcut=None):
        super(ResidualBlock, self).__init__()
        self.down = nn.Sequential(
            nn.Conv1d(inchannel, outchannel, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(outchannel),
            nn.ReLU(),
            nn.Conv1d(outchannel, outchannel, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(outchannel),
            nn.ReLU(),
            nn.Conv1d(outchannel, outchannel, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm1d(outchannel),
            nn.ReLU(),
        )
        self.up = shortcut

    def forward(self, x):
        out = self.down(x)
        residual = x if self.up is None else self.up(x)
        out = residual + out
        out = F.relu(out)
        return out


class ESTCNN_ResNet(nn.Module):
    def __init__(self):
        super(ESTCNN_ResNet, self).__init__()

        self.conv1 = nn.Sequential(
            nn.Conv1d(25, 25, 3, stride=1, padding=0, bias=False),
            nn.BatchNorm1d(25),
            nn.ReLU(),
            nn.Conv1d(25, 25, 3, stride=1, padding=0, bias=False),
            nn.BatchNorm1d(25),
            nn.ReLU(),
            nn.Conv1d(25, 25, 3, stride=1, padding=0, bias=False),
            nn.BatchNorm1d(25),
            nn.ReLU(),
        )

        self.layer1 = self.__make__layer(25, 32, 1)
        self.layer2 = self.__make__layer(32, 64, 1)
    

        self.rnn = nn.LSTM(
            input_size=11,
            hidden_size=128,
            num_layers=2,
            batch_first=True
        )
        self.fc2 = nn.Linear(128, 3)

    def __make__layer(self, inchannel, outchannel, block_num, stride=1):
        shortcut = nn.Sequential(
            nn.Conv1d(inchannel, outchannel, 1, stride=1, padding=0, bias=False),
            nn.BatchNorm1d(outchannel)
        )
        layers = []
        layers.append(ResidualBlock(inchannel, outchannel, stride, shortcut))

        for i in range(1, block_num):
            layers.append(ResidualBlock(outchannel, outchannel))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.layer1(x)
        x = self.layer2(x)
        r_out, (h_n, h_c) = self.rnn(x, None)
        x = r_out[:, -1, :]
        x = self.fc2(x)
        return x

def train_model(model, train_loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    # Calculate average loss and accuracy
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


# valid
def validate(model, criterion, val_loader, device):
    total_loss = 0
    total = 0
    model.eval()
    with torch.no_grad():
        for data, target in val_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            total += target.size(0)
            total_loss += loss.item()
    avg_loss = total_loss / total
    return avg_loss


# test
def evaluate_model(model, test_loader, device):
    model.eval()
    correct = 0
    total = 0
    true_labels = []
    predicted_labels = []

    with torch.no_grad():
        for data, label in test_loader:
            data, label = data.to(device), label.to(device)
            outputs = model(data)
            pred = torch.max(outputs, 1)[1]
            total += label.size(0)
            correct += (pred == label).sum().item()
            true_labels.extend(label.cpu().numpy())
            predicted_labels.extend(pred.cpu().numpy())

    acc = 100. * correct / total
    f1 = f1_score(true_labels, predicted_labels, average='macro')
    precision = precision_score(true_labels, predicted_labels, average='macro', zero_division="warn")
    recall = recall_score(true_labels, predicted_labels, average='macro')

    return acc, f1, precision, recall



def main():
    num_epochs = 100
    lr = 0.001
    batch_size = 25
    num_folds = 5
    num_subjects = 23
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    overall_acc_sum = 0
    overall_f1_sum = 0
    overall_precision_sum = 0
    overall_recall_sum = 0

    for subject_id in range(1, num_subjects + 1):
        setup_seed(44)
        print(f"Processing subject {subject_id}/{num_subjects}")
        train_loaders, val_loaders, test_loader = load_dataset(subject_id, batch_size, num_folds)
        model = ESTCNN_ResNet().to(device)
        optimizer = optim.Adam(model.parameters(), lr=lr)
        criterion = nn.CrossEntropyLoss()
        model.apply(weigth_init)
        acc_sum = 0
        f1_sum = 0
        precision_sum = 0
        recall_sum = 0
        for epoch in range(num_epochs):
            for fold, (train_loader, val_loader) in enumerate(zip(train_loaders, val_loaders)):
                train_loss, train_acc = train_model(model, train_loader, criterion, optimizer, device)
                val_loss = validate(model, criterion, val_loader, device)
                test_acc, f1, precision, recall = evaluate_model(model, test_loader, device)
                acc_sum += test_acc
                f1_sum += f1
                precision_sum += precision
                recall_sum += recall
                # print(f"Subject {subject_id}, Fold {fold + 1}/{num_folds}, Epoch {epoch + 1}/{num_epochs}, Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, Val Loss: {val_loss:.4f}")
                print(f"Subject {subject_id}, Fold {fold + 1}/{num_folds}, Epoch {epoch + 1}/{num_epochs}, Test Acc: {test_acc:.4f}, F1 Score: {f1:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}")

        acc_mean = acc_sum / (num_epochs * num_folds)
        f1_mean = f1_sum / (num_epochs * num_folds)
        precision_mean = precision_sum / (num_epochs * num_folds)
        recall_mean = recall_sum / (num_epochs * num_folds)

        print(
            f'Subject {subject_id} Mean: ACC:{acc_mean:.4f},F1:{f1_mean:.4f},Recall:{recall_mean:.4f},Precision:{precision_mean:.4f}')

     
        overall_acc_sum += acc_mean
        overall_f1_sum += f1_mean
        overall_precision_sum += precision_mean
        overall_recall_sum += recall_mean


    overall_acc_mean = overall_acc_sum / num_subjects
    overall_f1_mean = overall_f1_sum / num_subjects
    overall_precision_mean = overall_precision_sum / num_subjects
    overall_recall_mean = overall_recall_sum / num_subjects

    print(f"total: Test Acc: {overall_acc_mean:.4f}, F1 Score: {overall_f1_mean:.4f}, Precision: {overall_precision_mean:.4f}, Recall: {overall_recall_mean:.4f}")


if __name__ == '__main__':
    main()
