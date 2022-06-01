title: 一些用一次忘一次的 SQL 管理指令
date: 2021/01/11
path: 2021/01/11
---

有些 SQL 伺服器的管理指令是在剛架起來的時候比較常用到，或是有時會在 MySQL/PostgreSQL 間切換，所以幾乎都查一次忘一次。

## 安裝及啟動

### MySQL

在 Fedora 上的指令似乎會自動變成 MariaDB, XD

```
# On Fedora or RHEL variants
sudo dnf install mysql-server
# Or on Ubuntu, Debian variants
sudo apt install mysql-server
```

安裝完成後設定 root 密碼以及確認刪除一些 MySQL 內建的測試內容

```
mysql_secure_installation
```

Client 的 root user 連線方式目前預設是只會檢查本地的 unix username ，因此不能直接用 3306 port 連線，要使用 sudo

```
sudo mysql
```

### PostgreSQL

```
# Fedora 上如果不是一定要最新版的話這個就可以
sudo dnf install postgresql-server
# On Ubuntu
sudo apt install postgresql postgresql-contrib
```

安裝完成後預設的認證方式是 `ident` ，也是透過檢查 unix username 進行認證，因此一開始需要切換至 postgresql 建立的 `postgres` user

```
sudo su postgres
psql
```

## 允許連線

### MySQL

編輯 `/etc/mysql/my.cnf` 或 `/etc/mysql/mysql.conf.d/mysqld.conf` 下的 `bind-address`

### PostgreSQL

`/var/lib/pgsql/data` (或 `/var/lib/pgsql/<版本>/data`) 下的 `postgresql.conf` 下的 `listen_addresses` 及 `port` 設定

以及 `pg_hba.conf` ，以允許所有 user 透過 TCP socket 連上本地 IP 來說，可以使用如下的設定

```
host    replication     all             127.0.0.1/32            ident
```

## 資料庫、資料表顯示、切換

### MySQL

列出所有資料庫

```
show databases;
```

切換資料庫

```
use dbname;
```

列出所有資料表

```
show tables;
```

查看資料表欄位

```
describe tablename;
```

### PostgreSQL

列出所有資料庫

```
\l
# Or for more information
\l+
# Or using SELECT
SELECT datname FROM pg_database;
```

切換資料庫

```
\c dbname
```

列出所有資料表

```
\dt
```

查看資料表欄位

```
SELECT table_name,column_name,data_type 
FROM information_schema.columns 
WHERE table_name='tablename';
```

## 使用者及權限

### MySQL

對於認證方式，有些應用程式（例如文章寫成時的 PHP mysqli）需要使用舊版的認證方式，需要在 `/etc/mysql/my.cnf` 加入
：

```
default-authentication-plugin=mysql_native_password
```

對於使用者則需要確認是使用對應的驗證方式：

```
ALTER USER 'user'@'localhost' IDENTIFIED BY 'mysql_native_password' WITH '密碼';
```

### PostgreSQL

新增使用者、更改使用者密碼：

```
CREATE USER 'user' WITH PASSWORD '密碼';
ALTER USER 'user' WITH PASSWORD '密碼';
```

### 差不多的部分

對於使用者寫表等等的權限，可以使用 `GRANT` 語句：
```
GRANT ALL ON db1.* TO 'jeffrey'@'localhost';
GRANT SELECT, CREATE, REFERENCE, DELETE, RELOAD ON db1.* TO 'user'@'localhost';
```

## References

[PostgreSQL: Documentation: 13: Authentication Methods](https://www.postgresql.org/docs/13/auth-methods.html)

[PostgreSQL: Documentation: 13: The pg_hba.conf File](https://www.postgresql.org/docs/13/auth-pg-hba-conf.html)

[MySQL :: MySQL 8.0 Reference Manual :: 13.7.1.6 GRANT Statement](https://dev.mysql.com/doc/refman/8.0/en/grant.html)

[PostgreSQL Show Tables](https://www.postgresqltutorial.com/postgresql-show-tables/)

[PostgreSQL DESCRIBE TABLE](https://www.postgresqltutorial.com/postgresql-describe-table/)