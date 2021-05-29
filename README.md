# FTPU: a simple FTP file uploader

## 目的
FTPを用いてウェブサイトに必要なファイルを自動でアップロードするツール。

## コマンド
pythonを用いて実行する。基本的な操作は次の３つ。

- connect: ディレクトリをホストサーバに接続する。
- update: 接続されたホストサーバに、ディレクトリの状況を反映させる。
- *config: 設定をいじる。ホストサーバの名称、ユーザ、パスワードを保存、管理、変更する。* config機能は現在開発中。

### connectコマンド

```
python path/to/ftpu.py connect
```

ディレクトリの接続先をconfigに登録する。CLIを用いてホスト名、サーバのユーザ名、パスワードを入力し、それをローカルのconfigに保存する。

### updateコマンド

```
python path/to/ftpu.py <files>
```

ディレクトリの内容を設定されたホストサーバに反映させる。<files>を指定すると、そのファイルやディレクトリのみを反映させる。

## config
`$HOME/ffftpy-config.json`に保存されたjson設定ファイルに、FTP接続に必要な情報を保存する。この設定ファイルのことをconfigと呼ぶ。
configは次の形式で保存される。

```
{
    "dirname":{
        "host": <hostserver name>,
        "user": <username>,
        "password": <raw password>,
    }
}
```

