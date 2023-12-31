import gymnasium as gym
import numpy as np
from PIL import Image
import os
import random


class NormalizedObsWrapper(gym.ObservationWrapper):
    def __init__(self, env, **kwargs):
        super().__init__(env, **kwargs)
        self.observation_space = gym.spaces.Box(
            low=0,
            high=1,
            shape=self.env.unwrapped.observation_space.shape,
            dtype=np.float32,
        )

    def observation(self, observation):
        return observation / (
            self.env.unwrapped.grid_size_h * self.env.unwrapped.grid_size_w
        )


class OneHotEncodingWrapper(gym.ObservationWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.observation_space = gym.spaces.Box(
            low=0,
            high=1,
            shape=(
                self.env.unwrapped.grid_size_h
                * self.env.unwrapped.grid_size_w
                * self.env.unwrapped.grid_size_h
                * self.env.unwrapped.grid_size_w,
            ),
            dtype=np.float32,
        )

    def observation(self, obs):
        one_hot_encoded = np.zeros(self.observation_space.shape)
        for i in range(self.env.unwrapped.grid_size_h):
            for j in range(self.env.unwrapped.grid_size_w):
                tile_value = obs[i, j]
                one_hot_index = i * self.env.unwrapped.grid_size_w + j
                one_hot_encoded[
                    one_hot_index
                    * self.env.unwrapped.grid_size_h
                    * self.env.unwrapped.grid_size_w
                    + tile_value
                ] = 1
        return one_hot_encoded


class ImagePuzzleWrapper(gym.ObservationWrapper):
    def __init__(self, env, image_folder="img", image_size=(200, 200)):
        super(ImagePuzzleWrapper, self).__init__(env)
        self.image_folder = image_folder
        self.image_size = image_size
        self.section_size = (
            image_size[0] // self.env.unwrapped.grid_size_h,
            image_size[1] // self.env.unwrapped.grid_size_w,
        )
        self.image_sections = []
        self.load_random_image()

    def load_random_image(self):
        images = os.listdir(self.image_folder)
        random_image_path = os.path.join(self.image_folder, random.choice(images))
        image = Image.open(random_image_path).resize(self.image_size)
        self.split_image(image)

    def split_image(self, image):
        self.image_sections = []
        for i in range(self.env.unwrapped.grid_size_h):
            for j in range(self.env.unwrapped.grid_size_w):
                left = j * self.section_size[1]
                upper = i * self.section_size[0]
                right = left + self.section_size[1]
                lower = upper + self.section_size[0]
                section = image.crop((left, upper, right, lower))
                self.image_sections.append(section)

    def observation(self, obs):
        new_image = Image.new("RGB", self.image_size)
        for i in range(self.env.unwrapped.grid_size_h):
            for j in range(self.env.unwrapped.grid_size_w):
                section_idx = obs[i, j]
                if section_idx != 0:
                    section = self.image_sections[section_idx]
                    new_image.paste(
                        section, (j * self.section_size[1], i * self.section_size[0])
                    )
        return np.array(new_image)

    def render(self, mode="human"):
        if self.env.unwrapped.render_mode in ["human", "rgb_array"]:
            current_obs = self.env.unwrapped.state
            img_obs = self.observation(current_obs)
            img = Image.fromarray(img_obs, 'RGB')

            if self.env.unwrapped.render_mode == "rgb_array":
                return np.array(img)

            self.env.unwrapped.ax.imshow(img)
            self.env.unwrapped.fig.canvas.draw()
            self.fig.canvas.flush_events()

        elif self.env.unwrapped.render_mode == "state":
            return self.env.unwrapped.state
