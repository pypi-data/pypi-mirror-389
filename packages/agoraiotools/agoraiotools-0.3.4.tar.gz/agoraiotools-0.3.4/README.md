# Authenticate Users with a token


```
APP_ID = "{APP_ID}"
APP_CERTIFICATE = "{APP_CERTIFICATE}"


from agoraiotools.ChatTokenBuilder2 import ChatTokenBuilder

expire = 3600
user_id = "test_user"
#generateUserToken
token = ChatTokenBuilder.build_user_token(APP_ID, APP_CERTIFICATE, user_id, expire)


#generateAppToken
token = ChatTokenBuilder.build_app_token(APP_ID, APP_CERTIFICATE, expire)
```


Pypi
https://pypi.org/project/agoraiotools/
