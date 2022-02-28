# 個人チャット

DBもセキュリティーも整備できたので、次はどんどんエンドポイントを実装して行けばアプリが完成されます。

あくまでも個人的な（実務経験がない人の）やり方ですが、私は基本的に以下のような流れでエンドポイントを開発します。

1. 機能と仕様の設計
2. リクエストとリスポンスのモデルの実装
3. crud操作の実装
4. エンドポイントの実装

ちなみに実際では、フロントエンドとバックエンドが同時に開発していることが多いので、最初にインターフェースを決めることが一番大事です。どんなエンドポイントを提供するか、各エンドポイントはどんな形のデータでやり取りするか、それを決めないと、何もはじまりません。

今回は個人チャットのパートでは、以下6つのエンドポイントを実装していきます。

- ユーザ登録
- ログイン（ユーザ情報取得）
- フレンド追加
- フレンド情報取得
- チャットの送信
- チャット履歴の取得

実際の仕様はこの章の[最後](##仕様)にまとめて記載しますので、挑戦したい人はそこから作ってみてください。

## 仕様

### ユーザ登録
- path: `/user/register`
- method: POST
- 機能：新しいユーザをDBに登録する
- リクエストスキーマ:application/json
```json
{
  "username": "string",
  "password": "string"
}
```
- レスポンススキーマ: application/json
```json
{
  "id": 0,
  "username": "string"
}
```

### フレンド情報取得
- path: `/user/get_friends`
- method: GET
- 機能：ログインしているユーザのフレンド情報を取得する
- レスポンススキーマ: application/json
```json
[
  {
    "id": 0,
    "username": "string"
  },
  {
    "id": 0,
    "username": "string"
  }
]
```

### フレンド追加
- path: `/user/add_friend`
- method: POST
- 機能: ログインしているユーザのフレンドリストに新しいユーザを追加する
- リクエストスキーマ:application/json
```json
{
  "friend_id": 0
}
```
- レスポンススキーマ: application/json
  - 新しいフレンドリストを返す
  - フレンド情報取得と同じ

### ログイン（ユーザ情報取得）
- path: `/login`
- method: GET
- 機能：ログインしているユーザのユーザ情報を取得する
- レスポンススキーマ: application/json
```json
{
  "id": 0,
  "username": "string",
  "friends": [] // フレンド情報と同じ
}
```

### チャットの送信
- path: `/message/send_personal_chat`
- method: POST
- 機能：メッセージを送信する、wsでその内容を自分と相手（ログインしている場合は）に送信する
- リクエストスキーマ:application/json
```json
{
  "datetime": "2019-08-24T14:15:22Z",
  "receiver_id": 0,
  "message": "string"
}
```
- レスポンススキーマ: `'Succeed'`
- wsの送信スキーマ
```json
{
    "personal_message": {
        "id": 0,
        "datetime": "2019-08-24T14:15:22Z",
        "sender_id": 0,
        "receiver_id": 0,
        "message": "string"
    }
}

```

### チャット履歴の取得
- path: `/message/personal_chat_history`
- 機能: ログインしているユーザと相手のチャット履歴を取得する
- method: GET
- クエリパラメータ: 
  - receiver_id: int
    - 相手のユーザID
  - skip: int
    - 取得するチャット履歴の最初の位置
  - limit: int
    - 取得するチャット履歴の最大件数
  - desc: bool
    - true: 降順
    - false: 昇順
- レスポンススキーマ: application/json
```json
[
    {
        "id": 0,
        "datetime": "2019-08-24T14:15:22Z",
        "sender_id": 0,
        "receiver_id": 0,
        "message": "string"
    },
    {
        "id": 0,
        "datetime": "2019-08-24T14:15:22Z",
        "sender_id": 0,
        "receiver_id": 0,
        "message": "string"
    }
]
```
