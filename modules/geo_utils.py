import math

class GeoUtils:
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        # Formule de Haversine pour la distance en km
        R = 6371 
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * 
             math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def calculate_bearing(lat1, lon1, lat2, lon2):
        # Calcule l'angle (0-360°) entre deux points
        rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
        rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
        dlon = rlon2 - rlon1
        
        y = math.sin(dlon) * math.cos(rlat2)
        x = math.cos(rlat1) * math.sin(rlat2) - \
            math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360

    @staticmethod
    def bearing_to_cardinal(bearing):
        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        ix = round(bearing / (360. / len(dirs))) % len(dirs)
        return dirs[ix]
