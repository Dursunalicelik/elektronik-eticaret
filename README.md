# NovaStore – Flask E-ticaret Projesi

Orta ölçekli başlangıç e-ticaret uygulaması. Ödeme entegrasyonu yoktur; kullanıcılar sipariş oluşturabilir.

## Kurulum (Windows / PowerShell)

1. Proje klasörünü VS Code ile aç.
2. Terminali aç ve sanal ortam oluştur:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

3. Tarayıcıda `http://127.0.0.1:5000` adresini aç.

## Demo yönetici hesabı

- E-posta: `admin@novastore.local`
- Şifre: `NovaAdmin123!`

Bu hesap yalnızca yerel geliştirme içindir. Gerçek yayına almadan önce şifreyi değiştir, SECRET_KEY değerini güvenli bir ortam değişkeninden ver ve güvenlik kontrollerini güçlendir.

## Özellikler

- Ürün listeleme, kategori ve metin araması, sıralama
- Ürün detay sayfası
- Sepet ekleme, adet güncelleme, kaldırma
- Kullanıcı kaydı ve girişi (şifreler hash'lenir)
- Ödeme almadan sipariş oluşturma
- Sipariş geçmişi
- Yönetici paneli: ürün ekleme/silme, sipariş durumunu güncelleme

## Notlar

Bu proje eğitim ve portföy başlangıcıdır. Gerçek kullanıma açmadan önce CSRF koruması, form doğrulama, rate limiting, güvenli oturum/anahtar yönetimi, görsel yükleme kontrolleri, testler ve dağıtım ayarları eklenmelidir.
