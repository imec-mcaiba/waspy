import requests
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import widgets, dates, ticker


class Graph:
    def __init__(self):
        title_string = "Detector: " + sys.argv[1]
        self.fig = plt.figure(title_string)
        self.title_text = plt.figtext(0.20, 0.94, title_string, size='x-large', color='blue')
        ax_size = [0.11, 0.20, 1-0.140, 1-0.27] # [left, bottom, width, height] as fractions of figure width and height.
        self.axes = self.fig.add_axes(ax_size)
        self.reset_axes()
        self.pause = False

    def set_play_pause(self, animation):
        self.pause = not self.pause
        if self.pause:
            animation.pause()
        else:
            animation.resume()

    def reset_axes(self):
        self.axes.clear()
        self.axes.set_xlabel("Energy Level")
        self.axes.set_ylabel("Occurrence")
        self.axes.grid(which='both')
        self.axes.yaxis.set_ticks_position('left')
        self.axes.xaxis.set_ticks_position('bottom')
        # self.axes.xaxis_date()
        # self.axes.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
        # self.axes.xaxis.set_major_locator(ticker.AutoLocator())

    def consume_data(self, data):
        if data is None:
            print("No data available !!")
            self.axes.set_facecolor('lightgrey')
            self.axes.get_lines()[0].set_color("black")
            return
        else:
            self.axes.set_facecolor('white')
        self.reset_axes()
        self.axes.plot(data)

    def get_data(self):
        while True:
            try:
                data = requests.get("http://mill.capitan.imec.be/api/rbs/caen/detector/{}".format(sys.argv[1])).json()
            except Exception as e:
                data = None
            yield data



if __name__ == "__main__":
    graph = Graph()
    ani = animation.FuncAnimation(graph.fig, graph.consume_data,
                                  frames=graph.get_data(),
                                  interval=1200,
                                  repeat=True,
                                  cache_frame_data=False,
                                  blit=False)

    graph.day_button = widgets.Button(plt.axes([0.84, 0.01, 0.15, 0.060]), 'play/pause')
    graph.day_button.on_clicked(lambda _: graph.set_play_pause(ani))
    plt.show()
