"""
LSTM Model for Sequence-based Product Recommendation
Dự đoán sản phẩm tiếp theo dựa trên chuỗi hành vi của user
"""

import os
import logging
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from django.conf import settings

logger = logging.getLogger(__name__)


class ProductSequenceDataset(Dataset):
    """Dataset cho chuỗi hành vi user"""

    def __init__(self, sequences, targets, product_to_idx):
        self.sequences = sequences
        self.targets = targets
        self.product_to_idx = product_to_idx

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        seq = self.sequences[idx]
        target = self.targets[idx]

        # Convert to indices
        seq_indices = [self.product_to_idx.get(p, 0) for p in seq]
        target_idx = self.product_to_idx.get(target, 0)

        return torch.tensor(seq_indices, dtype=torch.long), torch.tensor(target_idx, dtype=torch.long)


class LSTMRecommender(nn.Module):
    """
    LSTM Model cho product recommendation

    Architecture:
    - Embedding layer: chuyển product_id thành vector
    - LSTM layers: học patterns từ sequence
    - Fully connected: dự đoán product tiếp theo
    """

    def __init__(self, num_products, embedding_dim=64, hidden_dim=128, num_layers=2, dropout=0.2):
        super(LSTMRecommender, self).__init__()

        self.num_products = num_products
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # Embedding layer
        self.embedding = nn.Embedding(
            num_embeddings=num_products + 1,  # +1 for padding/unknown
            embedding_dim=embedding_dim,
            padding_idx=0
        )

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Attention layer
        self.attention = nn.Linear(hidden_dim, 1)

        # Output layers
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_dim // 2, num_products + 1)

    def forward(self, x):
        # x shape: (batch_size, seq_len)

        # Embedding
        embedded = self.embedding(x)  # (batch_size, seq_len, embedding_dim)

        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)  # lstm_out: (batch_size, seq_len, hidden_dim)

        # Attention mechanism
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)  # (batch_size, seq_len, 1)
        context = torch.sum(attention_weights * lstm_out, dim=1)  # (batch_size, hidden_dim)

        # Fully connected layers
        out = self.fc1(context)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)  # (batch_size, num_products)

        return out

    def get_embeddings(self, product_ids):
        """Lấy embeddings cho các products"""
        with torch.no_grad():
            indices = torch.tensor(product_ids, dtype=torch.long)
            return self.embedding(indices).numpy()


class LSTMEngine:
    """
    Engine quản lý LSTM model cho recommendations
    """

    SEQUENCE_LENGTH = 10  # Độ dài chuỗi hành vi

    def __init__(self):
        self.model = None
        self.product_to_idx = {}
        self.idx_to_product = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = getattr(settings, 'MODEL_DIR', '.') / 'lstm_recommender.pt' if hasattr(settings, 'MODEL_DIR') else 'lstm_recommender.pt'

    def _build_sequences(self, interactions_df):
        """
        Xây dựng chuỗi hành vi từ interactions

        Args:
            interactions_df: DataFrame với columns [user_id, product_id, timestamp]

        Returns:
            sequences: List of product sequences
            targets: List of target products (next product)
        """
        sequences = []
        targets = []

        # Group by user và sort by timestamp
        for user_id, group in interactions_df.groupby('user_id'):
            products = group.sort_values('created_at')['product_id'].tolist()

            # Tạo sliding window sequences
            for i in range(len(products) - self.SEQUENCE_LENGTH):
                seq = products[i:i + self.SEQUENCE_LENGTH]
                target = products[i + self.SEQUENCE_LENGTH]
                sequences.append(seq)
                targets.append(target)

        return sequences, targets

    def _build_vocab(self, interactions_df):
        """Xây dựng vocabulary cho products"""
        unique_products = interactions_df['product_id'].unique()

        # Index 0 reserved for padding/unknown
        self.product_to_idx = {str(p): i + 1 for i, p in enumerate(unique_products)}
        self.idx_to_product = {i + 1: str(p) for i, p in enumerate(unique_products)}

    def train(self, epochs=50, batch_size=64, learning_rate=0.001):
        """
        Train LSTM model

        Returns:
            dict: Training statistics
        """
        from .models import UserInteraction
        import pandas as pd

        logger.info("Starting LSTM training...")

        # Load interactions
        interactions = UserInteraction.objects.all().values(
            'user_id', 'product_id', 'created_at'
        )
        df = pd.DataFrame(list(interactions))

        if df.empty or len(df) < 100:
            logger.warning("Not enough data for LSTM training")
            return {'status': 'insufficient_data', 'count': len(df)}

        # Convert UUIDs to strings
        df['user_id'] = df['user_id'].astype(str)
        df['product_id'] = df['product_id'].astype(str)

        # Build vocabulary
        self._build_vocab(df)
        num_products = len(self.product_to_idx)

        # Build sequences
        sequences, targets = self._build_sequences(df)

        if len(sequences) < 50:
            logger.warning("Not enough sequences for training")
            return {'status': 'insufficient_sequences', 'count': len(sequences)}

        logger.info(f"Training with {len(sequences)} sequences, {num_products} products")

        # Create dataset and dataloader
        dataset = ProductSequenceDataset(sequences, targets, self.product_to_idx)

        # Split train/val
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Initialize model
        self.model = LSTMRecommender(
            num_products=num_products,
            embedding_dim=64,
            hidden_dim=128,
            num_layers=2
        ).to(self.device)

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

        best_val_loss = float('inf')
        train_losses = []
        val_losses = []

        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            for batch_seq, batch_target in train_loader:
                batch_seq = batch_seq.to(self.device)
                batch_target = batch_target.to(self.device)

                optimizer.zero_grad()
                output = self.model(batch_seq)
                loss = criterion(output, batch_target)
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

                optimizer.step()
                train_loss += loss.item()

            avg_train_loss = train_loss / len(train_loader)
            train_losses.append(avg_train_loss)

            # Validation
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for batch_seq, batch_target in val_loader:
                    batch_seq = batch_seq.to(self.device)
                    batch_target = batch_target.to(self.device)

                    output = self.model(batch_seq)
                    loss = criterion(output, batch_target)
                    val_loss += loss.item()

            avg_val_loss = val_loss / len(val_loader) if val_loader else 0
            val_losses.append(avg_val_loss)

            scheduler.step(avg_val_loss)

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                self._save_model()

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")

        logger.info(f"LSTM training completed. Best val loss: {best_val_loss:.4f}")

        return {
            'status': 'success',
            'epochs': epochs,
            'num_products': num_products,
            'num_sequences': len(sequences),
            'best_val_loss': best_val_loss,
            'train_losses': train_losses[-5:],
            'val_losses': val_losses[-5:]
        }

    def predict(self, user_id, n=10):
        """
        Dự đoán sản phẩm tiếp theo cho user

        Args:
            user_id: ID của user
            n: Số sản phẩm trả về

        Returns:
            List of (product_id, score) tuples
        """
        if self.model is None:
            self._load_model()

        if self.model is None:
            return []

        from .models import UserInteraction

        # Get recent interactions
        recent = UserInteraction.objects.filter(
            user_id=user_id
        ).order_by('-created_at')[:self.SEQUENCE_LENGTH]

        if not recent.exists():
            return []

        # Build sequence
        products = [str(r.product_id) for r in reversed(list(recent))]

        # Pad if necessary
        while len(products) < self.SEQUENCE_LENGTH:
            products.insert(0, '')

        # Convert to indices
        seq_indices = [self.product_to_idx.get(p, 0) for p in products[-self.SEQUENCE_LENGTH:]]

        # Predict
        self.model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor([seq_indices], dtype=torch.long).to(self.device)
            output = self.model(input_tensor)
            probabilities = torch.softmax(output, dim=1)[0]

        # Get top-n predictions
        top_indices = torch.topk(probabilities, n + len(products)).indices.cpu().numpy()

        results = []
        seen = set(products)
        for idx in top_indices:
            if idx in self.idx_to_product:
                product_id = self.idx_to_product[idx]
                if product_id not in seen:
                    score = probabilities[idx].item()
                    results.append({
                        'product_id': product_id,
                        'score': score,
                        'reason': 'Dự đoán từ LSTM'
                    })
                    if len(results) >= n:
                        break

        return results

    def get_product_embeddings(self, product_ids):
        """Lấy LSTM embeddings cho products"""
        if self.model is None:
            self._load_model()

        if self.model is None:
            return None

        indices = [self.product_to_idx.get(str(p), 0) for p in product_ids]
        return self.model.get_embeddings(indices)

    def _save_model(self):
        """Lưu model và vocab"""
        if self.model is None:
            return

        model_dir = os.path.dirname(self.model_path)
        if model_dir and not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)

        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'product_to_idx': self.product_to_idx,
            'idx_to_product': self.idx_to_product,
            'num_products': self.model.num_products,
            'embedding_dim': self.model.embedding_dim,
            'hidden_dim': self.model.hidden_dim
        }
        torch.save(checkpoint, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def _load_model(self):
        """Load model từ file"""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file not found: {self.model_path}")
            return

        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)

            self.product_to_idx = checkpoint['product_to_idx']
            self.idx_to_product = checkpoint['idx_to_product']

            self.model = LSTMRecommender(
                num_products=checkpoint['num_products'],
                embedding_dim=checkpoint['embedding_dim'],
                hidden_dim=checkpoint['hidden_dim']
            ).to(self.device)

            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()

            logger.info("LSTM model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading LSTM model: {e}")
            self.model = None


# Singleton instance
lstm_engine = LSTMEngine()
