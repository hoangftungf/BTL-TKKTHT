AI Service cho tư vấn sản phẩm
3.1 Mục tiêu
Xây dựng hệ thống AI gợi ý sản phẩm dựa trên:
 Hành vi người dùng (click, search, add-to-cart)
 Quan hệ sản phẩm (similarity)
 Ngữ cảnh truy vấn (chatbot)
Output:
 Danh sách sản phẩm đề xuất
 Chatbot tư vấn
3.2 Kiến trúc AI Service
AI Service được thiết kế như một microservice độc lập:
 Input: user behavior, query
 Processing:
– LSTM model
– Knowledge Graph
– RAG
 Output: recommendation / chatbot response
3.3 Thu thập dữ liệu
3.3.1 User Behavior Data
 user_id
 product_id
 action (view, click, add_to_cart)
 timestamp

3.3.2 Ví dụ dataset
user_id , product_id , action , time
1 , 101 , view , t1
1 , 102 , add_to_cart , t2
3.4 Mô hình LSTM (Sequence Modeling)
3.4.1 Ý tưởng
Dự đoán sản phẩm tiếp theo dựa trên chuỗi hành vi.
3.4.2 Model chi tiết
import torch
import torch . nn as nn
class LSTMModel ( nn . Module ) :
def __init__ ( self , input_dim =10 , hidden_dim =64 , output_dim
=100) :
super () . __init__ ()
self . lstm = nn . LSTM ( input_dim , hidden_dim , batch_first =
True )
self . fc = nn . Linear ( hidden_dim , output_dim )
def forward ( self , x ) :
out , _ = self . lstm ( x )
out = out [: , -1 , :]
return self . fc ( out )
3.4.3 Training
criterion = nn . CrossEntropyLoss ()
optimizer = torch . optim . Adam ( model . parameters () )
for epoch in range ( epochs ) :
output = model ( x )
loss = criterion ( output , y )
loss . backward ()
optimizer . step ()
3.5 Knowledge Graph với Neo4j
3.5.1 Mô hình đồ thị
 Node: User, Product
 Edge:
22
– BUY
– VIEW
– SIMILAR
3.5.2 Ví dụ Cypher
CREATE ( u : User { id :1})
CREATE ( p : Product { id :101})
CREATE ( u ) -[: BUY ] - >( p )
3.5.3 Truy vấn gợi ý
MATCH ( u : User { id :1}) -[: BUY ] - >( p ) -[: SIMILAR ] - >( rec )
RETURN rec
3.6 RAG (Retrieval-Augmented Generation)
3.6.1 Pipeline
 Retrieve:
– Tìm sản phẩm liên quan từ DB / vector DB
 Generate:
– Sinh câu trả lời bằng LLM
3.6.2 Vector Database
 FAISS / ChromaDB
 Embedding từ mô tả sản phẩm
3.6.3 Ví dụ
query = " laptop gaming "
results = vector_db . search ( query )
response = LLM . generate ( results )
3.7 Kết hợp Hybrid Model
 LSTM: dự đoán hành vi
 Graph: quan hệ sản phẩm
 RAG: hiểu ngữ nghĩa
Final Recommendation:
final_score = w1 * lstm + w2 * graph + w3 * rag
23
3.8 Hai dạng AI Service
3.8.1 1. Recommendation List
Use cases
 Khi search
 Khi add-to-cart
API
GET / recommend ? user_id =1
Output
[101 , 102 , 205]
3.8.2 2. Chatbot tư vấn
Input
"tôi cần laptop giá rẻ"
Pipeline
 NLP hiểu intent
 Retrieve sản phẩm
 Generate response
API
POST / chatbot
Output
"Bạn có thể tham khảo Laptop XYZ giá 10 triệu..."
3.9 Triển khai AI Service
3.9.1 Tech stack
 tensorflow/PyTorch (LSTM)
 Neo4j (Graph)
 FAISS (Vector DB)
 FastAPI (service)
24
3.9.2 Kiến trúc
 AI service độc lập
 Giao tiếp với các service khác qua API
3.10 Bài tập
 Xây dựng model LSTM đơn giản
 Tạo graph trong Neo4j
 Implement API recommendation
 Xây dựng chatbot cơ bản
3.11 Checklist đánh giá
 Có pipeline AI rõ ràng
 Có model (LSTM)
 Có Graph và RAG
 Có API hoạt động
3.12 Kết luận
 AI giúp cá nhân hóa trải nghiệm
 Kết hợp nhiều mô hình cho hiệu quả cao
 Phù hợp hệ e-commerce hiện đại
