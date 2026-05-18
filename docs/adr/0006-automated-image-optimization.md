---
codd:
  node_id: "req:adr-0006"
  type: adr
  status: accepted
  links:
    - to: src/infrastructure/image_optimizer.py
      type: implementation
  evidence: "src/infrastructure/image_optimizer.py EXISTS and integrated into SupabaseRepository._sync_photos"
---

# ADR 0006: 自動画像最適化（WebPパイプライン）の導入

## ステータス

承認済み

## コンテキスト

VLogプロジェクトでは、VRChat内での活動を記録した画像アセット（PNG）が蓄積されています。現在の画像ファイルは平均1.2MB〜1.4MBであり、モバイル環境での閲覧時にデータ通信量とLCP（Largest Contentful Paint）に悪影響を及ぼしています。

今後のアセット増加に伴い、ストレージ容量の圧迫と配信コストの増大が予想されるため、配信の軽量化（「軽緑化」）が必要です。

## 決定事項

以下の画像最適化パイプラインを実装し、配信の軽量化を自動化します。

1. **WebP変換の自動化**:
   * `src/infrastructure/image_optimizer.py` を新設し、Pillowを使用して PNG から WebP への変換を実装する。
   * 品質（quality）は視覚的な劣化を最小限に抑えつつ、ファイルサイズを劇的に削減できる `80` 前後をデフォルトとする。

2. **同期プロセスへの統合**:
   * `SupabaseRepository._sync_photos` において、PNGを直接アップロードする代わりに、WebP変換後のバイナリを優先的にアップロードするように変更する。
   * ストレージ上のパスを `photos/{date}.webp` とし、Content-Type を `image/webp` に設定する。

3. **フォールバック設計**:
   * 変換環境（Pillowの有無など）に依存せず、失敗時はオリジナルのPNGを使用する弾力性を確保する。

## 期待される効果

* 画像ファイルサイズの約90%削減（1.2MB -> 0.1MB程度）。
* Web UIの読み込み速度（LCP）の大幅な改善。
* モバイルデータ通信環境での快適な閲覧体験の提供。

## 代替案の検討

* **CDN側での自動最適化**: Cloudflare Images 等の外部サービス利用も検討したが、現状の Supabase Storage を活かしつつ、ビルド/同期時に最適化を行う方がコスト効率と柔軟性が高いと判断した。
