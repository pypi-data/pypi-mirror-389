import pathlib
import uritools

class FileUriHandler:
    """
    putting this as a separate class from file based node data writers
    so that we have a separation of concerns
    on how file URIs are handled and data format
    """

    @staticmethod
    def generate_file_url(file_name, output_path, is_parent_location=True):
        """
        if is_parent_location is set to True,
        then output_path is the directory that would contain the output file
        and we need to append the base file name
        """
        parts = uritools.urisplit(output_path)

        path = parts.path
        if is_parent_location is True:
            path = (pathlib.Path(path) / file_name).as_posix()

        data_url = uritools.uricompose(scheme=parts.scheme,
                                       host=parts.host,
                                       port=parts.port,
                                       path=path)

        return data_url

    @staticmethod
    def generate_parent_url(output_path):
        parts = uritools.urisplit(output_path)
        path = parts.path
        parent_path = pathlib.Path(path).parent.as_posix()
        parent_url = uritools.uricompose(scheme=parts.scheme,
                                       host=parts.host,
                                       port=parts.port,
                                       path=parent_path)

        return parent_url

    # END class FileUriHandler
    pass