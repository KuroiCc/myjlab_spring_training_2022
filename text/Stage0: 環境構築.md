# Stage0: 環境構築

今回の課題はdockerを使って、仮想環境を構築して行います。macOSやWindowsでは、アプリケーション開発の手順が違いますので、それを避けるため仮想環境でOS違いを吸収します。

環境構築とかdockerとかは初めての人にとっては正直難しいと思うので、わからなかったらどうぞ質問してください。

開発するエディタはVS Codeを推奨します。ここからダウンロードすることができます。

<https://azure.microsoft.com/ja-jp/products/visual-studio-code/>

## dockerをインストールする

- [Macの場合]()
- [Windowsの場合]()

## 必要なファイルを準備

1. 以下のリンクから環境構築に使うファイルをダウンロードする

* <https://github.com/KuroiCc/myjlab_spring_training_2022>
* 画像は別のリポジトリになりますが、右の方にある緑色の Clone or download ボタンから ZIP を選択
<img width="1200" alt="Download zip" src="https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/clone-zip.png">

2. zip ファイルを*デスクトップ*に移動

3. zipファイルを展開する

# 使用方法

## 起動

1. ターミナルでダウンロードしたファイルがある場所に移動( *$は入力しなくて良い* )

```bash
$ cd
$ cd Desktop
$ cd myjlab_spring_training_2022-main/chat_app
```

2. Dockerコンテナ起動( *$は入力しなくて良い* )

```bash
$ docker-compose up
```

3. *注意* 初回はかなり時間がかかるので，下記のログが出力されるまではしばらく待機

![20220219123001](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220219123001.png)

## 停止

1. `docker-compose up` コマンドを実行したウィンドウで `Ctrl + c`


## 動作確認

1. 起動中に`http://localhost:8080`にアクセス

2. 下記の画面が表示されれば完了

![20220219123052](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220219123052.png)
