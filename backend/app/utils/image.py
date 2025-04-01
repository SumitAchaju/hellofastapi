from PIL.ImageFile import ImageFile


def resize_image(img: ImageFile, size: tuple[int, int]) -> ImageFile:
    width, height = img.size
    resize_width, resize_height = size
    if width < resize_width or height < resize_height:
        return img
    else:
        aspect_ratio = width / height

        if aspect_ratio > 1:
            new_height = resize_height
            new_width = int(new_height * aspect_ratio)
            return img.resize((new_width, new_height))
        else:
            new_width = resize_width
            new_height = int(new_width / aspect_ratio)
            return img.resize((new_width, new_height))
