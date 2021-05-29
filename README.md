# FFFT.py(仮称)　仕様書

## 目的
FTPを用いてウェブサイトに必要なファイルを自動でアップロードするツール。

## コマンド
pythonを用いて実行する。基本的な操作は次の３つ。

- connect: ディレクトリをホストサーバに接続する。
- update: 接続されたホストサーバに、ディレクトリの状況を反映させる。
- config: 設定をいじる。ホストサーバの名称、ユーザ、パスワードを保存、管理、変更する。

### connectコマンド

```
python scripts/ffftpy/ffft.py connect
```

ディレクトリの接続先をconfigに登録する。CLIを用いてホスト名、サーバのユーザ名、パスワードを入力し、それをローカルのconfigに保存する。

### updateコマンド

```
python scripts/ffftpy/ffft.py update <files>
```

ディレクトリの内容を設定されたホストサーバに反映させる。<files>を指定すると、そのファイルやディレクトリのみを反映させる。

### configコマンド

```
python scripts/ffftpy/ffft.py config <property/operation> <new value>
```

configのpropertyをnew valueに置き換える。operationとは、connectとupdate以外の重要なコマンドのことで、設定の削除や逆コピーなどを行うことができる。

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

