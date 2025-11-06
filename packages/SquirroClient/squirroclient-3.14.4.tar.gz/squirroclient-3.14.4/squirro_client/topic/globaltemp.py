import os
import re
from urllib.parse import quote


class GlobalTempMixin:
    def _encode_header(self, value):
        """Encode value for safe inclusion in HTTP headers.

        This function encodes value using percent-encoding to ensure that it is UTF-8
        compatible. This is necessary because HTTP headers are not able to natively
        carry characters outside of the ISO-8859-1 character set as mentioned in
        RFC 5987.

        :param value: Value to be encoded for use in an HTTP header.
        """
        # Replace spaces different than default one (\u0020) which break search results
        # and chips functionality
        spaces_to_replace = "[\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000]"
        value = re.sub(spaces_to_replace, " ", value)

        encoded_value = quote(value, safe="")
        # Add UTF-8 extended notation mentioned in RFC 5987
        return f"UTF-8''{encoded_value}"

    def new_tempfile_from_localfile(self, filename, index_pdf=None):
        """Stores the file identified by `file_name` on Squirro's global temp
        folder.

        :param filename: Name of the file on local filesystem to be uploaded to
            the server
        :param index_pdf: Whether to enable PDF chunk indexing. If None, auto-detects PDF files.
        """
        if not os.path.exists(filename):
            raise ValueError(f"Can not find file {filename}")

        data = open(filename, "rb").read()

        # Auto-detect PDF files if index_pdf not specified
        if index_pdf is None:
            index_pdf = filename.lower().endswith(".pdf")

        return self.new_tempfile(
            data=data, filename=os.path.basename(filename), index_pdf=index_pdf
        )

    def new_tempfile(self, data, filename=None, index_pdf=False):
        """Stores the `data` in a temp file.

        :param data: data to be stored in the temp file
        :param filename: optional filename, serving as metadata of the temp file.
        :param index_pdf: whether to enable PDF chunk indexing for PDF files.
        """

        url = f"{self.topic_api_url}/v0/{self.tenant}/temp"
        headers = {}
        if filename is not None:
            headers["X-Filename"] = self._encode_header(filename)
        if index_pdf:
            headers["X-Index-PDF"] = "true"

        res = self._perform_request("post", url, files={"file": data}, headers=headers)
        return self._process_response(res, [201])

    def get_tempfile(self, filename, file_type=None):
        """Returns the content of the temp file with the name `filename`.

        :param filename: File name
        :param file_type: The type of file- for community uploads, these values are
            either `community_csv` or `community_xlsx`
        """

        url = f"{self.topic_api_url}/v0/{self.tenant}/temp"
        res = self._perform_request(
            "get", url, params={"filename": filename, "file_type": file_type}
        )
        if res.status_code == 200:
            return res.content
        else:
            return self._process_response(res)
