import logging.config
 
def logging_config():
	logging.config.dictConfig({ 
		'version': 1,
		'disable_existing_loggers': False,
		'formatters': { 
			'standard': { 
					'format': '%(asctime)s [%(levelname)-7s] %(name)s: %(message)s',
					'datefmt': '%Y-%m-%d %H:%M',
			},
			'colored': {
				'()': 'colorlog.ColoredFormatter',
				# 'format': "%(log_color)s%(levelname)-8s%(reset)s %(message)s"
				'format': "%(log_color)s%(levelname)-8s %(message)s"
			}		
		},
		'handlers': { 
			'default': { 
				'level': 'DEBUG',
				'formatter': 'colored',
				'class': 'logging.StreamHandler',
			},
		},
		'loggers': { 
			'': { 
				'handlers': ['default'],
				'level': 'DEBUG',
				'propagate': True
			},
			'django.request': { 
				'handlers': ['default'],
				'level': 'WARN',
				'propagate': False
			},
		} 
	})