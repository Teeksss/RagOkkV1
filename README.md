# RAG System

Gelişmiş Alım Artırılmış Üretim (Retrieval Augmented Generation - RAG) sistemi, farklı dilleri destekleyen, vektör indeksleme ve önbellekleme özelliklerine sahip güçlü bir bilgi erişim çözümü.

## 📋 Özellikler

- **Çok Dilli Destek**
  - Türkçe, İngilizce, Almanca, Fransızca, İspanyolca ve daha fazlası
  - Dil algılama ve dile özel vektör modelleri
  - Farklı dillerde doküman arama

- **Gelişmiş Vektör İndeksleme**
  - FAISS IVF ve HNSW indeksler
  - Otomatik performans optimizasyonu
  - Sharded indeksleme desteği

- **Doküman Sürüm Kontrolü**
  - Dokümanlardaki değişiklikleri takip etme
  - Önceki sürümlere erişim ve geri dönüş
  - Detaylı değişiklik karşılaştırması

- **Gelişmiş Önbellekleme**
  - Çoklu seviyeli önbellekleme mekanizmaları (Bellek, Disk, Redis)
  - TTL ve LRU cache stratejileri
  - Vektör sorguları için özelleştirilmiş önbellek

- **Kapsamlı Değerlendirme**
  - A/B test çerçevesi
  - Detaylı metrikler (doğruluk, kesinlik, anım)
  - Kullanıcı geri bildirimi analizi

## 🚀 Kurulum

### Ön Koşullar

- Python 3.9 veya üzeri
- PostgreSQL veya SQLite
- [Opsiyonel] Redis

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/yourusername/rag-system.git
cd rag-system
```

### 2. Sanal Ortam Oluşturun

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Çevresel Değişkenleri Ayarlayın

`.env` dosyası oluşturun:

```
# Uygulama ayarları
DEBUG=False
ENVIRONMENT=production
PORT=8000

# Veritabanı ayarları
DATABASE_URL=postgresql://user:password@localhost/ragdatabase

# Vektör indeksleme
EMBEDDINGS_MODEL=all-MiniLM-L6-v2
USE_GPU=True

# OpenAI (isteğe bağlı)
OPENAI_API_KEY=your-api-key-here

# Redis (isteğe bağlı)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 5. Veritabanını Hazırlayın

```bash
alembic upgrade head
```

### 6. Uygulamayı Çalıştırın

```bash
uvicorn rag_system.main:app --host 0.0.0.0 --port 8000
```

## 🐳 Docker ile Kurulum

Docker kullanarak sistemi tek bir komutla kurabilirsiniz:

```bash
docker-compose up -d
```

## 📖 Kullanım

### API Dokümantasyonu

API dokümantasyonuna şu adreslerden erişebilirsiniz:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Doküman Yükleme

```python
import requests

# API endpoint
url = "http://localhost:8000/documents/upload"

# Yetkilendirme
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Dosya yükleme
files = {"file": open("ornek_dokuman.pdf", "rb")}
data = {"title": "Örnek Doküman", "language": "tr"}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### Doküman Arama

```python
import requests

# API endpoint
url = "http://localhost:8000/search"

# Yetkilendirme
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

# Arama parametreleri
params = {
    "query": "yapay zeka nedir?",
    "k": 5
}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

## 🔧 Konfigürasyon

`rag_system/config.py` dosyasındaki `Settings` sınıfı üzerinden tüm sistem yapılandırmasını yönetebilirsiniz. Önemli yapılandırma seçenekleri:

| Parametre | Açıklama | Varsayılan Değer |
|-----------|----------|------------------|
| DATABASE_URL | Veritabanı bağlantı URI'si | sqlite:///./rag_system.db |
| EMBEDDINGS_MODEL | Gömme modeli | all-MiniLM-L6-v2 |
| MULTILINGUAL_MODEL | Çok dilli model | paraphrase-multilingual-MiniLM-L12-v2 |
| VECTOR_INDEX_PATH | Vektör indeksi için dosya yolu | ./data/vector_index |
| LLM_PROVIDER | LLM sağlayıcısı | openai |
| CACHE_TYPE | Önbellek türü (memory, redis, disk) | memory |

## 🧪 Testler

Testleri çalıştırmak için:

```bash
# Tüm testleri çalıştır
pytest

# Belirli bir modülü test et
pytest tests/test_vector_store.py

# Test kapsamını raporla
pytest --cov=rag_system
```

## 🌲 Proje Yapısı

```
rag_system/
├── api/                  # API rotaları ve bağımlılıkları
├── auth/                 # Kimlik doğrulama ve yetkilendirme
├── data_ingestion/       # Doküman işleme ve veri alımı
├── data_processing/      # Veri işleme ve vektör depolama
├── database/             # Veritabanı modelleri ve işlevleri
├── evaluation/           # Sistem değerlendirme ve metrikler
├── generation/           # Metin üretme ve LLM entegrasyonu
├── integration/          # Diğer sistemlerle entegrasyon
├── retrieval/            # Belge ve bilgi alımı
└── utils/                # Yardımcı araçlar
```

## 🚀 Üretim Ortamına Dağıtım

### Kubernetes ile Dağıtım

```bash
# Kubernetes namespace oluştur
kubectl create namespace rag-system

# Sırları uygula
kubectl apply -f deployment/kubernetes/secrets.yaml

# Veritabanı ve Redis dağıt
kubectl apply -f deployment/kubernetes/database-deployment.yaml
kubectl apply -f deployment/kubernetes/redis-deployment.yaml

# Ana uygulamayı dağıt
kubectl apply -f deployment/kubernetes/rag-deployment.yaml

# Otomatik ölçeklendirmeyi etkinleştir
kubectl apply -f deployment/kubernetes/horizontal-pod-autoscaler.yaml
```

### CI/CD Pipeline

GitLab CI/CD ile otomatik dağıtım için `deployment/ci-cd/gitlab-ci.yml` dosyasını kullanabilirsiniz.

## 🔄 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni özellik dalı oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: özelliğin kısa açıklaması'`)
4. Dalınızı uzak depoya push edin (`git push origin yeni-ozellik`)
5. Pull Request açın

## 📝 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.