import json
import requests
from typing import Any, List
from application_sdk.handlers import HandlerInterface


class PokeHandler(HandlerInterface):
    """
    Handler class for pokemon workflows
    """
    api_url: str = ""

    async def load(self, data: dict, **kwargs: Any) -> None:
        """
        Method to load the handler
        """
        self.api_url = data.get("apiUrl", "")

    async def test_auth(self, **kwargs: Any) -> bool:
        """
        Method to test the authentication / connection
        """
        if "pokeapi.co" in self.api_url:
            return True

        res = requests.get(self.api_url)
        res.raise_for_status()

        return True

    async def preflight_check(self, *args: List[Any], **kwargs: Any) -> Any:
        """
        Method to perform preflight checks
        """
        if "pokeapi.co" in self.api_url:
            return True

        res = requests.get(self.api_url)
        res.raise_for_status()

        return True

    async def fetch_metadata(self, **kwargs: Any) -> List[Any]:
        return self.__fetch_metadata(**kwargs)

    def __get_pokemon_habitats(self):
        url = "https://pokeapi.co/api/v2/pokemon-habitat"
        response = requests.get(url)
        response.raise_for_status()  # Ensure request was successful
        return response.json()["results"]

    def __get_pokemon_by_habitat(self, habitat_url: str):
        response = requests.get(habitat_url)
        response.raise_for_status()
        data = response.json()
        return [species for species in data.get("pokemon_species", [])]

    def __get_pokemon(self, pokemon_url: str):
        response = requests.get(pokemon_url)
        response.raise_for_status()
        return response.json()

    def __fetch_metadata(self, **kwargs: Any) -> List[Any]:
        metatype = kwargs.get("metadata_type", "")
        include_filter = kwargs.get("include_filter", "")
        exclude_filter = kwargs.get("exclude_filter", "")

        if include_filter:
            include_filter = json.loads(include_filter)
        else:
            include_filter = {}

        if exclude_filter:
            exclude_filter = json.loads(exclude_filter)
        else:
            exclude_filter = {}

        if metatype == "FilterTree":
            habitats = self.__get_pokemon_habitats()
            results = []
            
            for habitat in habitats:
                habitat_name = habitat["name"]
                habitat_url = habitat["url"]

                pokemons = self.__get_pokemon_by_habitat(habitat_url)
                for poke in pokemons:
                    results.append({"POKEMON_TYPE": habitat_name, "POKEMON": poke.get("name")})
            
            return results

        if metatype == "All":
            habitats = self.__get_pokemon_habitats()
            results = []

            for habitat in habitats:
                habitat_name = habitat['name']
                habitat_url = habitat["url"]

                if exclude_filter.get(habitat_name, []) == "*":
                    continue

                if include_filter and habitat_name not in include_filter:
                    continue

                pokemons = self.__get_pokemon_by_habitat(habitat_url)
                for poke in pokemons:
                    name = poke.get("name")
                    if include_filter.get(habitat_name) == "*":
                        results.append(self.__get_pokemon(poke.get("url")))
                        continue

                    if include_filter.get(habitat_name) and name not in include_filter.get(habitat_name):
                        continue

                    if exclude_filter.get(habitat_name) and name in exclude_filter.get(habitat_name):
                        continue

                    results.append(self.__get_pokemon(poke.get("url")))
            
            return results            

        return []

