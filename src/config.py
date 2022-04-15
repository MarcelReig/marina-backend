class Config:
    SECRET_KEY = 'ClaveSecreta!'

class DevelopmentConfig(Config):
    DEBUG=True


config={
  'development':DevelopmentConfig
}