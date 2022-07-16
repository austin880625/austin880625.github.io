```
sudo journalctl --vacuum-size=20M
sudo snap set system refresh.retain=2
```

```
#!/bin/bash
 #Removes old revisions of snaps
 #CLOSE ALL SNAPS BEFORE RUNNING THIS
 set -eu
 LANG=en_US.UTF-8 snap list --all | awk '/disabled/{print $1, $3}' |
     while read snapname revision; do
         snap remove "$snapname" --revision="$revision"
     done
```

```

```

https://www.debugpoint.com/clean-up-snap/
https://www.ibm.com/support/pages/how-clean-files-under-varspoolabrt-directory
https://forums.docker.com/t/some-way-to-clean-up-identify-contents-of-var-lib-docker-overlay/30604