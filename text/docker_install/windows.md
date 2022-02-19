# Windowsでの環境構築

## 参考ページ
なにかあればこちらの記事と照らし合わせるとよい

<https://github.com/marutaku/docker-fastapi-mysql-app/blob/master/docs/install-docker-windows.md>

## Dockerのダウンロード

1. [Docker Desktop](https://www.docker.com/products/docker-desktop)にアクセス

2. Download for Windowsをクリック

![Docker Desktop Mac](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/docker-desktop-page-win.png)

3. ダウンロードされたファイルをクリックして起動

4. インストールの開始，設定などには手を加えず，次に進んでいく

- もし下記の画面になったら[Windows Updateが必要な場合](#Windows-Updateが必要な場合)に進む

![install failed](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/docker_install_failed.png)

5. インストール完了

- もし下記の画面が出たら[WSL2の更新が必要な場合](#WSL2の更新が必要な場合)に進む

![wsl update](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/wsl2_done_restart.png)

4. Docker Desktopの起動

- 下記に似た画面が出たらインストール及び起動が完了
![install donw](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/docker-desktop.png)

## インストールの確認

### 1. コマンドプロンプトを起動
- 「Windowsキー」を押して「cmd」と入力して「Enter」を押して起動
- 「Windowsキー」を押して「コマンドプロンプト」を検索して起動

など

### 2. コマンドで確認( *$は入力しなくて良い* )

```bash
$ docker --version
$ docker-compose -verison
```

出力例

![](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/version.png)

## Windows Updateが必要な場合

1. [Windowsダウンロードのページ](https://www.microsoft.com/ja-jp/software-download/windows10IS://www.microsoft.com/ja-jp/software-download/windows10)に進み，下記のボタンからダウンロードする
![Windows Update](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/windows_update_page.png)

2. [元の手順](#Dockerのダウンロード)に戻る

## WSL2の更新が必要な場合

1. 下記の画面の *「restart」ではなく* リンクをクリック

![](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/install_wsl_kernel_link.png)

2. 開かれたページの下記のリンクをクリック

![](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/linux_update_download_page.png)

3. ダウンロードされたファイルを開いて，下記の画面が出たら特に変更なく進めていく

![](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/linux_setup.png)

4. 下記の画面まで進めれば完了

![](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/linux_setup_done.png)

5. 初めの画面の「restart」をクリックして再起動

![](https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/linux_update_download_page.png)

6. 再起動が完了したら[元の手順](#Dockerのダウンロード)に戻る