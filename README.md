# haproxy-service

### Setup Application
```
git clone git@github.com:LimeTray/haproxy-service.git
git checkout develop
cd haproxy-service
./hapservice setup

```
### Manage application
```
hapservice {start|stop|restart}
```

### Logs Path
```
/var/log/haproxy-service.log       # Application Logs
/var/log/haproxyservice-nohup.log  # Nohup output of process
```