# Macでの環境構築

## CPUの確認

「このMacについて」を開き，CPUを確認する．下記のどちらに当てはまるかを確認して進む
https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/intel.png
- Intelの場合は下記の画像  
  <img width="1200" alt="インテルの場合" src="https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/intel.png">
- Apple シリコンの場合は下記のリンク  
  [Apple シリコン搭載の Mac コンピュータ](https://support.apple.com/ja-jp/HT211814) 


## Dockerのダウンロード

1. [Docker Desktop](https://www.docker.com/products/docker-desktop)にアクセス

2. Intelの場合はMac with Intel Chip、Apple シリコンの場合はMac with Apple Chipをクリック

![20220219111938](https://raw.githubusercontent.com/KuroiCc/kuroi-image-host/main/images/20220219111938.png)

3. ダウンロードされたファイルをクリックして起動

4. Applicationsフォルダに移動
- ドラッグ&ドロップで移動する．完了したらウィンドウは閉じて良い
<img width="600" alt="Docker mac drag and drop" src="https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/drag-and-drop.png">

5. 起動
- Dockerを起動
  - アプリケーション → Dockerを起動
  - 「⌘ + スペース」で「Docker」と検索して起動

## インストールの確認

### 1. ターミナルを起動
- アプリケーション → その他 → ターミナルを起動
- 「⌘ + スペース」で「terminal」と検索して起動
など

### 2. コマンドで確認( *$は入力しなくて良い* )
```bash
$ docker --version
$ docker-compose -verison
```

出力例(Windowsの例なので出力が合っていれば良い)

<img width="600" alt="cmd.png" src="https://github.com/marutaku/docker-fastapi-mysql-app/raw/master/docs/images/version.png">
