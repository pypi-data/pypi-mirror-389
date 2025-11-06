from .structs._internal import Station, Departure, Operator, Arrival
import requests, typing
from .structs._internal import Journey as JourneyStruct, Polyline
from .structs import Filter, Products, Date
from datetime import datetime
from typing import Union, List
from urllib.parse import urlencode


class PyBahn(object):
    """
    PyBahn is a client library for accessing Deutsche Bahn's unofficial public APIs.

    It allows querying:
    - Journeys between two stations
    - Departures from a station
    - Arrivals at a station
    - Nearby station
    """

    def __init__(self):
        """
        Initialize a PyBahn client.

        No authentication or configuration is required.
        This prepares the client to make requests to the Bahn API.
        """
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Accept": "application/json"
        }
        self.date_format = "%Y-%m-%dT%H:%M:%S"

    def stations(self, name: str, limit: int = 10):
        """
        Searches for stations that match the given name and returns a list of Station objects.

        Args:
            name (str): The search keyword for station names.
            limit (int, optional): The maximum number of stations to return. Must be greater than 0. Defaults to 10.

        Returns:
            List[Station]: A list of Station objects matching the search criteria.

        Raises:
            ValueError: If the limit is less than 1.
            requests.RequestException: If the HTTP request fails.
        """

        if limit < 1:
            raise ValueError("Limit has to be more than 0")
        name = name.replace(" ", "+")
        url = f"https://int.bahn.de/web/api/reiseloesung/orte?suchbegriff={name}&typ=ALL&limit={limit}"

        response = requests.get(url, headers=self._headers)
        res_json: dict = response.json()
        _stations: typing.List[Station] = []

        for item in res_json:
            item: dict
            _stations.append(Station(name=item.get('name', ''), id=item.get('extId', ""), lid=item.get('id', ""), lat=item.get("lat", 0), lon=item.get('lon', 0), products=item.get('products', [])))
        
        return _stations

    def departures(self, station: typing.Union[Station, str], filters: typing.List[Filter] = [Filter.RB_RE], date: typing.Union[Date, datetime] = datetime.now()):
        """
        Returns a list of departures for a given station ID.

        Args:
            station (Station): The station object for which to retrieve departures.
            filters (Optional[List[Filter]], optional): List of transport types to include in the results (e.g., ['train', 'bus']). Default is None.
            date (Date, optional): The date to filter the departures. Default is now.

        Returns:
            List[Departure]: A list of `Departure` objects representing the departures from the station with the given `id`.
        """
        if isinstance(date, Date):
            date = datetime.fromisoformat(date.get())
            date = f"datum={date.strftime('%Y-%m-%d')}&zeit={date.strftime('%H:%M:%S')}"
        elif isinstance(date, datetime):
            date = f"datum={date.strftime('%Y-%m-%d')}&zeit={date.strftime('%H:%M:%S')}"

        if isinstance(station, Station):
            pass
        elif isinstance(station, str):
            station = self.station(station)
        else:
            raise ValueError("the station arg. must be an Station or String object")

        url_base = f"https://www.bahn.de/web/api/reiseloesung/abfahrten?{date}&ortExtId={station.id}&ortId={station.lid}&mitVias=false&maxVias=5"
        
        for filt in filters:
            url_base += filt

        response = requests.get(url_base, headers=self._headers)
        res_json = response.json()
        
        deps: typing.List[Departure] = []

        if res_json:
            for j in res_json['entries']:
                j['station_name'] = station.name
                deps.append(Departure(**j))
        return deps

    def arrivals(self, station: Union[str | int, Station], filters: typing.List[Filter] = [Filter.RB_RE], date: typing.Union[Date, datetime] = datetime.now()):
        if isinstance(date, Date):
            date = datetime.fromisoformat(date.get())
            date = f"datum={date.strftime('%Y-%m-%d')}&zeit={date.strftime('%H:%M:%S')}"
        elif isinstance(date, datetime):
            date = f"datum={date.strftime('%Y-%m-%d')}&zeit={date.strftime('%H:%M:%S')}"
            
        if isinstance(station, Station):
            pass
        elif isinstance(station, str) or isinstance(station, int):
            station = self.station(station)
        else:
            raise ValueError("the station arg. must be an Station or String or Int object")

        url_base = f"https://www.bahn.de/web/api/reiseloesung/ankuenfte?{date}&ortExtId={station.id}&ortId={station.lid}&mitVias=false&maxVias=5"

        for filt in filters:
            url_base += filt

        response = requests.get(url_base, headers=self._headers)
        res_json = response.json()
        deps: typing.List[Arrival] = []

        if res_json:
            for j in res_json['entries']:
                j['station_name'] = station.name
                deps.append(Arrival(**j))
        return deps
    
    def transport_way(self, journey_id: str, poly_lines: bool = False) -> List[Polyline]:
        url = "https://int.bahn.de/web/api/reiseloesung/verbindung"
        r = requests.post(url=url, headers=self._headers, json={
                "ctxRecon":journey_id, "poly":True,"polyWalk":True
            }
        )
        r.raise_for_status()
        data: list = r.json()['verbindungsAbschnitte'][0]['polylineGroup']['polylineDescriptions']
        return [Polyline(**d) for d in data]

    def journeys(self, departure: typing.Union[str, Station], destination: typing.Union[str, Station], date: typing.Union[str, Date] = "now", products: typing.Union[typing.List[Products], Products] = Products.ALL, only_d_ticket: bool = False, stopovers: List[Union[str, Station]] = []):
        """
        Retrieves a list of journey options between two locations.

        Args:
            departure (str): The location ID (LID) of the departure station(you can get it by using `station` function).
            destination (str): The location ID (LID) of the destination station(you can get it by using `station` function).
            time (str, optional): Desired departure time in ISO 8601 format (e.g., "2025-05-15T12:00:02"). 
                                If not provided (empty string), the current system time is used by default.
            products (Union[List[Products], Products], optional): Transport filters to limit the journey results 
                                (e.g., regional trains only). Can be a single product or a list. Defaults to `Products.REGIONALS`.
            only_d_ticket (bool, optional): If True, returns only journeys that are valid with the Deutschland-Ticket. Defaults to False.
            stopovers (List[Station], optional): List of stopovers stations, maximal is 2.
        """
        
        if isinstance(date, str):
            if date == "now":
                time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            else:
                datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
        
        elif isinstance(date, Date):
            time = date.get()
        
        url = "https://int.bahn.de/web/api/angebote/fahrplan"

        products = normalize_products(products)

        try:
            datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValueError("Wrong time format, please check again")
        

        data = {
            "abfahrtsHalt": departure if isinstance(departure, str) else departure.lid,
            "anfrageZeitpunkt": time,
            "ankunftsHalt": destination if isinstance(destination, str) else destination.lid,
            "ankunftSuche": "ABFAHRT",
            "klasse": "KLASSE_2",
            "produktgattungen": products,
            "reisende": [
                {
                    "typ": "JUGENDLICHER",
                    "ermaessigungen": [
                        {
                            "art": "KEINE_ERMAESSIGUNG",
                            "klasse": "KLASSENLOS"
                        }
                    ],
                    "alter": [],
                    "anzahl": 1
                }
            ],
            "schnelleVerbindungen": True,
            "sitzplatzOnly": False,
            "bikeCarriage": False,
            "reservierungsKontingenteVorhanden":False,
            "nurDeutschlandTicketVerbindungen": only_d_ticket,
            "deutschlandTicketVorhanden": False
        }

        if stopovers:
            if isinstance(stopovers, list):
                if len(stopovers) > 2:
                    raise ValueError("Too many stopovers, maximal is 2")
                else:
                    s_l_e_ = []

                    for d_sstop in stopovers:
                        if d_sstop.stopover_time and d_sstop.stopover_time > 0:
                            s_l_e_.append({
                                "id": d_sstop.lid,
                                "aufenthaltsdauer": d_sstop.stopover_time
                            })
                        else:
                            s_l_e_.append({
                                "id": d_sstop.lid
                            })

                    data['zwischenhalte'] = s_l_e_

            else:
                raise ValueError("Stopovers must be list even if only one")

        response = requests.post(url, headers=self._headers, json=data)
        res_json = response.json()
        journeys: typing.List[JourneyStruct] = []

        for jour in res_json['verbindungen']:
            __j = JourneyStruct(**jour)
            for conn in __j.connections:
                if not conn.means_of_transport.direction:
                    conn.means_of_transport.direction = conn.arrival_station
            journeys.append(__j)

        return journeys

    def operators(self):
        url = f"https://int.bahn.de/web/api/angebote/stammdaten/verbuende"
        response = requests.get(url, headers=self._headers)
        res_json = response.json()
        l: typing.List[Operator] = []
        for d in res_json:
            l.append(Operator(**d))
        
        return l

    def station(self, name: str):
        """
        Returns the first station that matches the given name.

        Args:
            name (str): The search keyword for the station name.

        Returns:
            Station: The first matching Station object.

        Raises:
            IndexError: If no stations are found.
        """
        station = self.stations(name, 2)
        if station[0].name.isupper():
            return station[1]
        else:
            return station[0]
    
    def nearby(self, latitude: float, longitude: float, limit=10):
        url = f"https://int.bahn.de/web/api/reiseloesung/orte/nearby?lat={latitude}&long={longitude}&radius=9999&maxNo={limit}"

        response = requests.get(url, headers=self._headers)
        res_json: dict = response.json()
        _stations: typing.List[Station] = []

        for item in res_json:
            item: dict
            _stations.append(Station(name=item.get('name', None), id=item.get('extId', None), lid=item.get('id', None), lat=item.get("lat", 0), lon=item.get('lon', 0), products=item.get('products', [])))
        
        return _stations
    
    def get_delay_minutes(self, scheduled: datetime, delayed: datetime) -> str:
        diff = int((delayed - scheduled).total_seconds() / 60)
        if diff == 0:
            return "On time"
        elif diff > 0:
            return f"+{diff} min"
        else:
            return f"{diff} min"
    

class Journey(object):
    """Journey object\n
    refer journey can fetch only: departure station, destination and departure time"""
    def __init__(self, refer: JourneyStruct = None):
        self.results: List[JourneyStruct] = None
        self._journeys = []
        if refer:
            dep = refer.connections[0].stopovers[0]
            self.__dep_station = Station(dep.station_name, dep.station_id, dep.id)
            dest = refer.connections[-1].stopovers[-1]
            self.__desti_station = Station(dest.station_name, dest.station_id, dest.id)

    def departure(self, station: Station):
        self.__dep_station = station
    
    def destination(self, station: Station):
        self.__desti_station = station
    
    def clear(self):
        self.__dep_station = None
        self.__desti_station = None

    def products(self, products: List[Union[str, Products]]):
        self.__products = products
    
    def search(self):
        self._journeys = PyBahn().journeys(
            departure=self.__dep_station, 
            destination=self.__desti_station, 
            products=self.__products if hasattr(self, "__products") and self.__products else Products.ALL
        )


__all__ = ["PyBahn"]



def normalize_products(products: Union[List[Union[Products, str]], Products, str]) -> List[str]:
    if isinstance(products, Products):
        products = products.value if isinstance(products.value, list) else [products.value]
    elif isinstance(products, list):
        result = []
        for item in products:
            if isinstance(item, Products) and isinstance(item.value, list):
                result.extend(item.value)
            elif isinstance(item, Products):
                result.append(item.value)
            elif isinstance(item, str):
                result.append(item)
        return result
    
    else:
        raise ValueError("Wrong `products` parameter, please check again")
    return products


if __name__ == "__main__":
    raise RuntimeError("This module is not intended to be run or imported directly.")
