```
CREATE USER IF NOT EXISTS 'wp_huonex' IDENTIFIED BY 'password';
CREATE DATABASE wp_huonex;
use wp_huonex
GRANT ALL PRIVILEGES ON wp_huonex.* TO 'wp_huonex';
```