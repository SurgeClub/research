import forecastio
from secrets import FORECAST_IO_API_KEY
import arrow


lat, lng = 37.7576171, -122.5776844

# time =
forecast = forecastio.load_forecast(FORECAST_IO_API_KEY, lat, lng, time=None, units="us" )

byHour = forecast.hourly()
print (byHour.summary)
print (byHour.icon)
# print (byHour.precipProbability)
