import base64
import io
import json
import sys
import traceback

import redis
from PIL import Image


class RedisBased:
    """
    Ancestor for classes that use Redis.
    """

    def __init__(self):
        """
        Initializes the manager
        """
        self.redis_connection = None
        self.redis_pubsub = None
        self.redis_thread = None

    def is_connected(self):
        """
        Checks whether we are currently connected to the redis backend.

        :return: True if connected
        :rtype: bool
        """
        return self.redis_connection is not None

    def connect(self, host, port, pw=None):
        """
        Connects to the redis backend.

        :param host: the redis host
        :type host: str
        :param port: the port of the redis server
        :type port: int
        :param pw: the password for the redis server, ignored if empty string or None
        :type pw: str
        :return: True if connection establised successfully
        :rtype: bool
        """
        if pw == "":
            pw = None
        self.redis_connection = redis.Redis(host=host, port=port, password=pw)
        try:
            self.redis_connection.ping()
            return True
        except:
            traceback.print_exc()
            self.redis_connection = None
            return False

    def disconnect(self):
        """
        Closes the Redis connection.

        :return:
        """
        try:
            self.redis_connection.close()
            self.redis_connection = None
        except:
            pass


class SamManager(RedisBased):
    """
    Obtains outline predictions from SAM (segment anything model).
    """

    def __init__(self):
        super().__init__()
        self.predictions = None

    def predict(self, image, points, channel_in, channel_out, min_obj_size, log, update):
        """
        Pushes the image through SAM and returns the normalized contours.

        :param image: the image as bytes
        :param points: the absolute points (list of x/y tuples)
        :type points: list
        :param channel_in: the channel to broadcast the SAM prompt on
        :type channel_in: str
        :param channel_out: the channel to receive the predictions on
        :type channel_out: str
        :param min_obj_size: the minimum size for the objects
        :type min_obj_size: int
        :param log: the method to use for logging string messages
        :param update: the method to call with predictions
        """
        prompt = {
            "points": [
                {
                    "x": item[0],
                    "y": item[1],
                    "label": 1
                } for item in points
            ]
        }

        # create message and send
        d = {
            "image": base64.encodebytes(image).decode("ascii"),
            "prompt": prompt,
        }
        self.redis_connection.publish(channel_in, json.dumps(d))

        self.redis_pubsub = self.redis_connection.pubsub()

        # handler for listening/outputting
        def anon_handler(message):
            log("SAM data received")
            d = json.loads(message['data'].decode())
            # mask
            png_data = base64.decodebytes(d["mask"].encode())
            mask = Image.open(io.BytesIO(png_data))
            width, height = mask.size
            # contours to normalized contours
            contours_n = []
            contours = d["contours"]
            discarded = 0
            if "meta" in d:
                meta = d["meta"]
            else:
                meta = dict()
            for contour in contours:
                points_n = []
                minx = sys.maxsize
                maxx = 0
                miny = sys.maxsize
                maxy = 0
                for coords in contour:
                    x, y = coords
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)
                    points_n.append((x / width, y / height))
                # minimum size?
                keep = (min_obj_size <= 0)
                if (min_obj_size > 0) and (maxx - minx + 1 > min_obj_size) and (maxy - miny + 1 > min_obj_size):
                    keep = True
                if keep:
                    contours_n.append(points_n)
                else:
                    discarded += 1
            log("# contours: %d" % len(contours_n))
            if discarded > 0:
                log("# contours too small (< %d): %d" % (min_obj_size, discarded))
            # stop/close pubsub
            self.redis_thread.stop()
            self.redis_pubsub.close()
            self.redis_pubsub = None
            # update contours/image
            self.predictions = contours_n
            self.meta = meta
            update(self.predictions, self.meta)

        # subscribe and start listening
        self.redis_pubsub.psubscribe(**{channel_out: anon_handler})
        self.redis_thread = self.redis_pubsub.run_in_thread(sleep_time=0.01)
