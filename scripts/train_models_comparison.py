"""
Bước 2a: Xây dựng 3 mô hình RNN, LSTM, biLSTM
- Train và đánh giá 3 mô hình
- So sánh và chọn model tốt nhất
- Visualization kết quả
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from sklearn.preprocessing import LabelEncoder

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Seed for reproducibility
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

# Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")


# ===================== DATASET =====================

class UserBehaviorDataset(Dataset):
    """
    Dataset cho chuỗi hành vi người dùng
    Input: Chuỗi các product_id đã tương tác
    Output: Product_id tiếp theo (next item prediction)
    """

    def __init__(self, sequences, targets):
        self.sequences = sequences
        self.targets = targets

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.sequences[idx], dtype=torch.long),
            torch.tensor(self.targets[idx], dtype=torch.long)
        )


def prepare_data(csv_path, sequence_length=10):
    """
    Chuẩn bị dữ liệu từ CSV

    Args:
        csv_path: Đường dẫn file CSV
        sequence_length: Độ dài chuỗi

    Returns:
        sequences, targets, product_encoder, action_encoder
    """
    print(f"\nLoading data from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Sort by timestamp
    df = df.sort_values(['user_id', 'timestamp'])

    # Encode products
    product_encoder = LabelEncoder()
    df['product_idx'] = product_encoder.fit_transform(df['product_id']) + 1  # +1 for padding

    # Encode actions (for potential multi-task learning)
    action_encoder = LabelEncoder()
    df['action_idx'] = action_encoder.fit_transform(df['action'])

    num_products = len(product_encoder.classes_)
    num_actions = len(action_encoder.classes_)

    print(f"  - Total records: {len(df):,}")
    print(f"  - Unique users: {df['user_id'].nunique()}")
    print(f"  - Unique products: {num_products}")
    print(f"  - Unique actions: {num_actions}")
    print(f"  - Sequence length: {sequence_length}")

    # Build sequences per user
    sequences = []
    targets = []

    for user_id, group in df.groupby('user_id'):
        product_indices = group['product_idx'].tolist()

        # Sliding window
        for i in range(len(product_indices) - sequence_length):
            seq = product_indices[i:i + sequence_length]
            target = product_indices[i + sequence_length]
            sequences.append(seq)
            targets.append(target)

    print(f"  - Total sequences: {len(sequences):,}")

    return (
        np.array(sequences),
        np.array(targets),
        product_encoder,
        action_encoder,
        num_products
    )


# ===================== MODELS =====================

class RNNRecommender(nn.Module):
    """Simple RNN Model"""

    def __init__(self, num_products, embedding_dim=64, hidden_dim=128, num_layers=2, dropout=0.2):
        super().__init__()
        self.model_name = "RNN"

        self.embedding = nn.Embedding(num_products + 1, embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_products + 1)
        )

    def forward(self, x):
        embedded = self.embedding(x)
        output, hidden = self.rnn(embedded)
        # Use last hidden state
        last_hidden = hidden[-1]
        return self.fc(last_hidden)


class LSTMRecommender(nn.Module):
    """LSTM Model"""

    def __init__(self, num_products, embedding_dim=64, hidden_dim=128, num_layers=2, dropout=0.2):
        super().__init__()
        self.model_name = "LSTM"

        self.embedding = nn.Embedding(num_products + 1, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Attention mechanism
        self.attention = nn.Linear(hidden_dim, 1)

        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_products + 1)
        )

    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(embedded)

        # Attention
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context = torch.sum(attention_weights * lstm_out, dim=1)

        return self.fc(context)


class BiLSTMRecommender(nn.Module):
    """Bidirectional LSTM Model"""

    def __init__(self, num_products, embedding_dim=64, hidden_dim=128, num_layers=2, dropout=0.2):
        super().__init__()
        self.model_name = "BiLSTM"

        self.embedding = nn.Embedding(num_products + 1, embedding_dim, padding_idx=0)
        self.bilstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Attention for bidirectional output
        self.attention = nn.Linear(hidden_dim * 2, 1)

        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_products + 1)
        )

    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.bilstm(embedded)

        # Attention over bidirectional output
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context = torch.sum(attention_weights * lstm_out, dim=1)

        return self.fc(context)


# ===================== TRAINING =====================

def train_epoch(model, dataloader, criterion, optimizer):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch_x, batch_y in dataloader:
        batch_x = batch_x.to(device)
        batch_y = batch_y.to(device)

        optimizer.zero_grad()
        output = model(batch_x)
        loss = criterion(output, batch_y)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()

        # Accuracy
        _, predicted = torch.max(output, 1)
        correct += (predicted == batch_y).sum().item()
        total += batch_y.size(0)

    return total_loss / len(dataloader), correct / total


def evaluate(model, dataloader, criterion):
    """Evaluate model"""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch_x, batch_y in dataloader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)

            output = model(batch_x)
            loss = criterion(output, batch_y)
            total_loss += loss.item()

            _, predicted = torch.max(output, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(batch_y.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)

    # Top-K accuracy
    top_k_acc = {}
    for k in [5, 10]:
        correct = 0
        model.eval()
        with torch.no_grad():
            for batch_x, batch_y in dataloader:
                batch_x = batch_x.to(device)
                batch_y = batch_y.to(device)
                output = model(batch_x)
                _, top_k_preds = torch.topk(output, k, dim=1)
                for i, label in enumerate(batch_y):
                    if label in top_k_preds[i]:
                        correct += 1
        top_k_acc[f'top_{k}'] = correct / len(dataloader.dataset)

    return avg_loss, accuracy, top_k_acc, all_preds, all_labels


def train_model(model, train_loader, val_loader, epochs=50, learning_rate=0.001):
    """
    Train a model and return training history
    """
    print(f"\n{'='*60}")
    print(f"Training {model.model_name}")
    print(f"{'='*60}")

    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=5, factor=0.5
    )

    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': [],
        'top_5_acc': [],
        'top_10_acc': []
    }

    best_val_loss = float('inf')
    best_model_state = None
    patience_counter = 0
    early_stop_patience = 10

    for epoch in range(epochs):
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer)

        # Validate
        val_loss, val_acc, top_k_acc, _, _ = evaluate(model, val_loader, criterion)

        # Scheduler step
        scheduler.step(val_loss)

        # History
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['top_5_acc'].append(top_k_acc['top_5'])
        history['top_10_acc'].append(top_k_acc['top_10'])

        # Best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            patience_counter = 0
        else:
            patience_counter += 1

        # Print progress
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | "
                  f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
                  f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | "
                  f"Top-5: {top_k_acc['top_5']:.4f} | Top-10: {top_k_acc['top_10']:.4f}")

        # Early stopping
        if patience_counter >= early_stop_patience:
            print(f"Early stopping at epoch {epoch + 1}")
            break

    # Load best model
    model.load_state_dict(best_model_state)

    return model, history


# ===================== VISUALIZATION =====================

def plot_training_history(histories, save_path):
    """Plot training history for all models"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    colors = {'RNN': '#e74c3c', 'LSTM': '#3498db', 'BiLSTM': '#2ecc71'}

    # 1. Training Loss
    ax = axes[0, 0]
    for name, hist in histories.items():
        ax.plot(hist['train_loss'], label=name, color=colors[name], linewidth=2)
    ax.set_title('Training Loss', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Validation Loss
    ax = axes[0, 1]
    for name, hist in histories.items():
        ax.plot(hist['val_loss'], label=name, color=colors[name], linewidth=2)
    ax.set_title('Validation Loss', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Training Accuracy
    ax = axes[0, 2]
    for name, hist in histories.items():
        ax.plot(hist['train_acc'], label=name, color=colors[name], linewidth=2)
    ax.set_title('Training Accuracy', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Validation Accuracy
    ax = axes[1, 0]
    for name, hist in histories.items():
        ax.plot(hist['val_acc'], label=name, color=colors[name], linewidth=2)
    ax.set_title('Validation Accuracy', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 5. Top-5 Accuracy
    ax = axes[1, 1]
    for name, hist in histories.items():
        ax.plot(hist['top_5_acc'], label=name, color=colors[name], linewidth=2)
    ax.set_title('Top-5 Accuracy', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 6. Top-10 Accuracy
    ax = axes[1, 2]
    for name, hist in histories.items():
        ax.plot(hist['top_10_acc'], label=name, color=colors[name], linewidth=2)
    ax.set_title('Top-10 Accuracy', fontsize=14, fontweight='bold')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.suptitle('Model Comparison: RNN vs LSTM vs BiLSTM', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved training plots to: {save_path}")


def plot_final_comparison(results, save_path):
    """Plot final comparison bar chart"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    models = list(results.keys())
    colors = ['#e74c3c', '#3498db', '#2ecc71']

    # 1. Accuracy comparison
    ax = axes[0]
    metrics = ['Accuracy', 'Top-5 Acc', 'Top-10 Acc']
    x = np.arange(len(metrics))
    width = 0.25

    for i, (model_name, res) in enumerate(results.items()):
        values = [res['accuracy'], res['top_5_acc'], res['top_10_acc']]
        bars = ax.bar(x + i * width, values, width, label=model_name, color=colors[i])
        # Add value labels
        for bar, val in zip(bars, values):
            ax.annotate(f'{val:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                       ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Score')
    ax.set_title('Accuracy Metrics Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.set_ylim(0, 1.0)
    ax.grid(True, axis='y', alpha=0.3)

    # 2. Loss comparison
    ax = axes[1]
    metrics = ['Final Val Loss', 'Best Val Loss']
    x = np.arange(len(metrics))

    for i, (model_name, res) in enumerate(results.items()):
        values = [res['final_val_loss'], res['best_val_loss']]
        bars = ax.bar(x + i * width, values, width, label=model_name, color=colors[i])
        for bar, val in zip(bars, values):
            ax.annotate(f'{val:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                       ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Loss')
    ax.set_title('Loss Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)

    plt.suptitle('Final Model Comparison', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Saved comparison chart to: {save_path}")


# ===================== MAIN =====================

def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'data_user500.csv')
    output_dir = os.path.join(base_dir, 'data', 'models')
    os.makedirs(output_dir, exist_ok=True)

    # Hyperparameters
    SEQUENCE_LENGTH = 10
    EMBEDDING_DIM = 64
    HIDDEN_DIM = 128
    NUM_LAYERS = 2
    DROPOUT = 0.2
    BATCH_SIZE = 64
    EPOCHS = 50
    LEARNING_RATE = 0.001

    print("="*60)
    print("BUOC 2a: TRAIN & COMPARE RNN, LSTM, BiLSTM")
    print("="*60)

    # 1. Load and prepare data
    sequences, targets, product_encoder, action_encoder, num_products = prepare_data(
        data_path, SEQUENCE_LENGTH
    )

    # 2. Create dataset and split
    dataset = UserBehaviorDataset(sequences, targets)
    train_size = int(0.7 * len(dataset))
    val_size = int(0.15 * len(dataset))
    test_size = len(dataset) - train_size - val_size

    train_dataset, val_dataset, test_dataset = random_split(
        dataset, [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(SEED)
    )

    print(f"\nDataset split:")
    print(f"  - Train: {len(train_dataset):,}")
    print(f"  - Val: {len(val_dataset):,}")
    print(f"  - Test: {len(test_dataset):,}")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # 3. Create models
    models = {
        'RNN': RNNRecommender(num_products, EMBEDDING_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT),
        'LSTM': LSTMRecommender(num_products, EMBEDDING_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT),
        'BiLSTM': BiLSTMRecommender(num_products, EMBEDDING_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT)
    }

    # Print model info
    print("\n" + "="*60)
    print("MODEL ARCHITECTURES")
    print("="*60)
    for name, model in models.items():
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"\n{name}:")
        print(f"  - Total parameters: {total_params:,}")
        print(f"  - Trainable parameters: {trainable_params:,}")

    # 4. Train all models
    histories = {}
    trained_models = {}

    for name, model in models.items():
        trained_model, history = train_model(
            model, train_loader, val_loader,
            epochs=EPOCHS, learning_rate=LEARNING_RATE
        )
        histories[name] = history
        trained_models[name] = trained_model

    # 5. Evaluate on test set
    print("\n" + "="*60)
    print("FINAL EVALUATION ON TEST SET")
    print("="*60)

    criterion = nn.CrossEntropyLoss()
    results = {}

    for name, model in trained_models.items():
        test_loss, test_acc, top_k_acc, preds, labels = evaluate(model, test_loader, criterion)

        results[name] = {
            'accuracy': test_acc,
            'top_5_acc': top_k_acc['top_5'],
            'top_10_acc': top_k_acc['top_10'],
            'final_val_loss': histories[name]['val_loss'][-1],
            'best_val_loss': min(histories[name]['val_loss']),
            'test_loss': test_loss
        }

        print(f"\n{name}:")
        print(f"  - Test Loss: {test_loss:.4f}")
        print(f"  - Accuracy: {test_acc:.4f}")
        print(f"  - Top-5 Accuracy: {top_k_acc['top_5']:.4f}")
        print(f"  - Top-10 Accuracy: {top_k_acc['top_10']:.4f}")

    # 6. Select best model
    print("\n" + "="*60)
    print("MODEL SELECTION")
    print("="*60)

    # Score based on multiple metrics
    scores = {}
    for name, res in results.items():
        # Weighted score: accuracy (40%) + top-5 (30%) + top-10 (20%) - loss (10%)
        score = (
            0.4 * res['accuracy'] +
            0.3 * res['top_5_acc'] +
            0.2 * res['top_10_acc'] -
            0.1 * res['test_loss'] / 5  # Normalize loss
        )
        scores[name] = score
        print(f"{name}: Composite Score = {score:.4f}")

    best_model_name = max(scores, key=scores.get)
    print(f"\n*** BEST MODEL: {best_model_name} ***")

    # 7. Save plots
    plot_training_history(histories, os.path.join(output_dir, 'training_history.png'))
    plot_final_comparison(results, os.path.join(output_dir, 'model_comparison.png'))

    # 8. Save best model
    best_model = trained_models[best_model_name]
    model_save_path = os.path.join(output_dir, 'model_best.pt')

    torch.save({
        'model_name': best_model_name,
        'model_state_dict': best_model.state_dict(),
        'num_products': num_products,
        'embedding_dim': EMBEDDING_DIM,
        'hidden_dim': HIDDEN_DIM,
        'num_layers': NUM_LAYERS,
        'sequence_length': SEQUENCE_LENGTH,
        'product_classes': list(product_encoder.classes_),
        'results': results[best_model_name]
    }, model_save_path)

    print(f"\nSaved best model to: {model_save_path}")

    # 9. Save all results
    results_path = os.path.join(output_dir, 'training_results.json')
    with open(results_path, 'w') as f:
        json.dump({
            'hyperparameters': {
                'sequence_length': SEQUENCE_LENGTH,
                'embedding_dim': EMBEDDING_DIM,
                'hidden_dim': HIDDEN_DIM,
                'num_layers': NUM_LAYERS,
                'dropout': DROPOUT,
                'batch_size': BATCH_SIZE,
                'epochs': EPOCHS,
                'learning_rate': LEARNING_RATE
            },
            'results': results,
            'best_model': best_model_name,
            'scores': scores
        }, f, indent=2)

    print(f"Saved results to: {results_path}")

    # 10. Print summary
    print("\n" + "="*60)
    print("SUMMARY - DANH GIA VA LUA CHON MO HINH")
    print("="*60)

    print("\n1. SO SANH 3 MO HINH:")
    print("-" * 50)
    print(f"{'Model':<10} {'Accuracy':<12} {'Top-5':<12} {'Top-10':<12} {'Loss':<10}")
    print("-" * 50)
    for name, res in results.items():
        print(f"{name:<10} {res['accuracy']:<12.4f} {res['top_5_acc']:<12.4f} "
              f"{res['top_10_acc']:<12.4f} {res['test_loss']:<10.4f}")

    print("\n2. DANH GIA:")
    print(f"""
    - RNN: Mo hinh don gian nhat, xu ly tuan tu mot chieu.
      Uu diem: Nhanh, it tham so. Nhuoc diem: Kho nho dai han.

    - LSTM: Them cell state va gates de xu ly long-term dependencies.
      Uu diem: Nho duoc thong tin dai han. Nhuoc diem: Cham hon RNN.

    - BiLSTM: Xu ly ca hai chieu (qua khu va tuong lai).
      Uu diem: Hieu context tot nhat. Nhuoc diem: Nhieu tham so nhat.
    """)

    print(f"3. KET LUAN:")
    print(f"   Model tot nhat: {best_model_name}")
    print(f"   Ly do: Dat diem tong hop cao nhat ({scores[best_model_name]:.4f})")
    print(f"   Accuracy: {results[best_model_name]['accuracy']:.4f}")
    print(f"   Top-10 Accuracy: {results[best_model_name]['top_10_acc']:.4f}")

    print("\n" + "="*60)
    print("HOAN THANH BUOC 2a!")
    print("="*60)
    print(f"\nOutput files:")
    print(f"  1. {os.path.join(output_dir, 'training_history.png')}")
    print(f"  2. {os.path.join(output_dir, 'model_comparison.png')}")
    print(f"  3. {model_save_path}")
    print(f"  4. {results_path}")


if __name__ == '__main__':
    main()
