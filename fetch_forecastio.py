import forecastio
from secrets import FORECAST_IO_API_KEY
import arrow

def get_preci_prob_by_loc_time(lat, lng, time):
    time = time.datetime
    forecast = forecastio.load_forecast(FORECAST_IO_API_KEY, lat, lng, time, units="us")
    byHour = forecast.currently()
    return byHour.precipProbability
