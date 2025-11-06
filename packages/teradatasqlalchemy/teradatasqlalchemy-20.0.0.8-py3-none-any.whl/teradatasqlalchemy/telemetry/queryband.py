from functools import wraps
import inspect
from teradatasqlalchemy import vernumber
import re


class QueryBand:
    """
    Class to hold the common attributes required for queryband enabling.
    """
    def __init__(self):
        self._qb_buffer = []
        self._org = "TERADATA-INTERNAL-TELEM"
        self._app_name = "TDSQLMY"
        self._app_version = vernumber.sVersionNumber
        self._qb_template = "QUERY_BAND='ORG={org};APPNAME={app_name};APPVERSION={app_version};{client_qb};'"
        self._set_qb_query_template = "SET {query_band} FOR TRANSACTION;"
        self._prev_qb_str = None
        self._prev_qb_str_freq = 0
        self._qb_regex = r'^[a-zA-Z0-9_-]+$'
        self._verbose = False
        self._optimize_queryband = False
        self._MAX_QB_KEY_VALUE = 256
        self._unflushed_buffers = []
        self._current_qb_length = 0

    @property
    def qb_buffer(self):
        """
        RETURNS:
            Queryband string.

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.qb_buffer
        """
        return self._qb_buffer

    @qb_buffer.setter
    def qb_buffer(self, query_band):
        """
        Creates query band buffer if it doesn't exist else appends query band
        to existing query band buffer self._qb_buffer.

        PARAMETERS:
            query_band

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.qb_buffer('ORG=TERADATA-INTERNAL-TELEM')
        """
        if not self._qb_buffer:
            self._qb_buffer = []
        self._qb_buffer.append(query_band)

    @property
    def qb_regex(self):
        """
        RETURNS:
            Regular expression which validates queryband string.

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.qb_regex
        """
        return self._qb_regex

    @property
    def verbose(self):
        """
        RETURNS:
            Configuration option which decides whether to print
            error logs on console or not.

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.verbose
        """
        return self._verbose

    @verbose.setter
    def verbose(self, verbose):
        """
        Sets configuration option which decides whether to print
        error logs on console or not.

        PARAMETERS:
            verbose

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.verbose(True)
        """
        self._verbose = verbose

    def append_qb(self, query_band):
        """
        DESCRIPTION:
            Appends queryband to queryband buffer. It also handles validation.
            In optimized mode, enables lazy flushing using unflushed_buffers.

        PARAMETERS:
            query_band:
                Required Argument.
                Specifies queryband string to append.
                Types: str

        RETURNS:
            None.

        RAISES:
            None.

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.append_qb('RmCxt')

        """
        if self._optimize_queryband:
            # When no lazy queryband is available, park current queryband.
            if not self._prev_qb_str:
                self._prev_qb_str = query_band
                self._prev_qb_str_freq = 1
            else:
                # check if queryband string is repeated.
                # If not, append _prev_qb_str to buffer and
                # update _prev_qb_str and _prev_qb_str_freq values
                # else just increase the frequency of previous queryband.
                if query_band != self._prev_qb_str:
                    # Process lazy queryband and park current queryband.
                    self._process_lazy_queryband()
                    self._prev_qb_str = query_band
                    # Update variables related to lazy processing.
                    self._prev_qb_str_freq = 1
                else:
                    self._prev_qb_str_freq = self._prev_qb_str_freq + 1
        else:
            self._validate_and_append(query_band)

    def pop_qb(self):
        """
        Removes last added queryband from query band buffer list.

        PARAMETERS:
            None

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.append_qb('RmCxt')
            >>> qb.pop_qb()

        """
        try:
            del self._qb_buffer[-1]
        except IndexError:
            self._qb_buffer = []

    def reset_qb(self):
        """
        Removes all querybands from query band buffer list.

        PARAMETERS:
            None

        EXAMPLES:
            >>> qb = QueryBand()
            >>> qb.append_qb('RmCxt')
            >>> qb.reset_qb()
        """
        self._prev_qb_str = None
        self._prev_qb_str_freq = 0
        self._qb_buffer = []
        self._unflushed_buffers = []
        self._current_qb_length = 0

    def configure_queryband_parameters(self, app_name, app_version):
        """
        DESCRIPTION:
            Configures application name and application version which
            uses queryband utility.

        PARAMETERS:
            app_name:
                Required Argument.
                Specifies name of the application which uses queryband utility.
                Types: str

            app_version:
                Required Argument.
                Specifies version of the application which uses queryband utility.
                Types: str

        RETURNS:
            None

        RAISES:
            None.

        EXAMPLES:
            >>> session_qb = QueryBand()
            >>> session_qb.configure_queryband_parameters(app_name="TDML", app_version="20.00.00.00")
        """
        self._app_name = app_name
        self._app_version = app_version

    def generate_set_queryband_queries(self, consume_all=False):
        """
        DESCRIPTION:
            Generates SQL queries to be used while setting transaction level
            queryband for an application. Application specific data and querybands
            collected during execution of application's APIs are used while generating
            final queryband string. If APPFUNC value exceeds 230 characters, it splits
            the buffer and returns multiple queries.

        PARAMETERS:
            consume_all:
            Specifies flag use all querybands from queryband buffer.

        RETURNS:
            list: List of SQL query strings

        RAISES:
            None.

        EXAMPLES:
            >>> session_qb = QueryBand()
            >>> queries = session_qb.generate_set_queryband_queries()
        """
        try:
            queries = []
            # Generate queries from unflushed buffers
            queries.extend(self._process_unflushed_buffers())

            # If optimization is not required or
            # full consumption of queryband is requested,
            # then consume pending queryband buffer as well.
            if not self._optimize_queryband or consume_all:
                # Before utilizing pending queryband buffer(_qb_buffer),
                # append lazy entries in _prev_qb_str to _qb_buffer.
                if self._prev_qb_str:
                    self._process_lazy_queryband()
                    self._prev_qb_str = None
                    self._prev_qb_str_freq = 0
                # Generate queries from unflushed buffers,
                # after processing of lazy queryband and append
                # to current set of queries.
                queries_from_unflushed_buffers = self._process_unflushed_buffers()
                if queries_from_unflushed_buffers:
                    queries.extend(queries_from_unflushed_buffers)

                # Generate queries from _qb_buffer.
                queries.append(self.prepare_set_qb_query(self._qb_buffer))
                # Reset queryband as everything is consumed.
                self.reset_qb()
            return queries
        except Exception as append_err:
            self.log("Failed to generate SET QB query: ", append_err)
            return []

    def prepare_set_qb_query(self, queyband_buffer):
        """
        DESCRIPTION:
            Generates SQL queries to be used while setting transaction level queryband.

        PARAMETERS:
            queyband_buffer:
                Specifies list of queryband strings to be concatenated.

        RETURNS:
            str

        RAISES:
            None.

        EXAMPLES:
            >>> session_qb = QueryBand()
            >>> session_qb.prepare_set_qb_query(["DF_concat", "CrtTbl"])
        """
        query = self._set_qb_query_template.format(
            query_band=self._qb_template.format(
                org=self._org,
                app_name=self._app_name,
                app_version=self._app_version,
                client_qb="APPFUNC={}".format("-".join(queyband_buffer))
            )
        )
        return query

    def log(self, *args):
        """
        DESCRIPTION:
            Prints error message on console if configuration option is enabled.

        PARAMETERS:
            Variable number of arguments each of string type.

        RETURNS:
            None

        EXAMPLES:
            >>> queryband_obj = QueryBand()
            >>> err_str = "SOME_ERR_IN_QUERYBAND"
            >>> queryband_obj.log("Failed to collect queryband.", err_str)
        """
        try:
            if self.verbose:
                print(*args)
        except Exception as log_err:
            if self.verbose:
                print("Failed to log error in queryband:", log_err)

    def optimize_flush(self):
        """
        DESCRIPTION:
             Enables optimized flushing of queryband strings by setting internal flag.

        PARAMETERS:
            None.

        RETURNS:
            None.

        RAISES:
            None.

        EXAMPLES:
            # Set queryband using SQLalchemy connection object from application.
            >>> queryband_obj = QueryBand()
            >>> queryband_obj.optimize_flush()
        """
        self._optimize_queryband = True

    def execute_set_queryband(self, con_obj):
        """
        DESCRIPTION:
             Executes set queryband SQL request using connection object from application
             and then clears queryband buffer for next workflow.

        PARAMETERS:
            con_obj:
                Required Argument.
                Specifies connection object to execute string.
                Types: Sqlalchemy connection

        RETURNS:
            None.

        RAISES:
            None.

        EXAMPLES:
            # Set queryband using SQLalchemy connection object from application.
            >>> queryband_obj = QueryBand()
            >>> queryband_obj.execute_set_queryband(con_obj=conn)
        """
        # Execute set queryband SQL request.
        try:
            queries = self.generate_set_queryband_queries()
            for query in queries:
                con_obj.exec_driver_sql(query)
            self.reset_qb()
        except Exception as qb_err:
            self.log("Failed to set QB!!!", qb_err)

    def _get_lazy_queryband_string(self):
        """
        Internal utility function for processing lazy queryband
        along with frequency of its repetitive occurrence.
        """
        if self._prev_qb_str:
            # If _prev_qb_str is having frequency more than 1, then append queryband
            # string with frequency, else append without frequency.
            return self._prev_qb_str + "_" + str(self._prev_qb_str_freq) \
                if self._prev_qb_str_freq > 1 else self._prev_qb_str

    def _validate_and_append(self, queryband_to_append):
        """
        Internal utility method for validating and appending queryband string to existing buffer.
        It checks if processing of current queryband string violates queryband's allowed limit,
        if so, moves current queryband into unflushed buffer and reinitializes variables related
        to queryband buffer.
        """
        if not queryband_to_append or not isinstance(queryband_to_append, str):
            self.log("Invalid value passed for queryband: {}".format(queryband_to_append))
            return False

        if len(queryband_to_append) > self._MAX_QB_KEY_VALUE:
            self.log("Length {} of queryband string '{}' exceeds maximum character limit of {}.".format(
                len(queryband_to_append),queryband_to_append,self._MAX_QB_KEY_VALUE))
            return False

        # Check if processing of current queryband string violates
        # queryband's allowed limit, if so,
        # move current queryband into unflushed buffer and
        # reinitialize queryband buffer related variables.
        if (self._current_qb_length + len(queryband_to_append)) > self._MAX_QB_KEY_VALUE:
            self._unflushed_buffers.append(self._qb_buffer)
            self._qb_buffer = []
            self._current_qb_length = 0

        # Append queryband string and update length.
        self._qb_buffer.append(queryband_to_append)
        self._current_qb_length += len(queryband_to_append) + 1
        return True

    def _process_lazy_queryband(self):
        """
        Internal utility method for validating and appending lazy queryband string to existing queryband buffer.
        """
        # Process lazy queryband.
        if self._prev_qb_str:
            lazy_processed = self._validate_and_append(self._get_lazy_queryband_string())
            # Try without appending frequency to tackle char limit issue.
            if not lazy_processed:
                self._validate_and_append(self._prev_qb_str)

    def _process_unflushed_buffers(self):
        """
        Internal utility method for processing unflushed buffer.
        """
        queries = []
        for unflushed_buffer in self._unflushed_buffers:
            queries.append(self.prepare_set_qb_query(unflushed_buffer))
        self._unflushed_buffers = []
        return queries


def collect_queryband(session_queryband, queryband=None, attr=None, method=None,
                      arg_name=None, prefix=None, suffix=None):
    """
    DESCRIPTION:
        Decorator for collecting queryband string in queryband buffer.

    PARAMETERS:
        session_queryband:
            Required Argument.
            Specifies Queryband object to be used to process and store queryband strings.
            Types: Teradatasqlalchemy QueryBand

        queryband:
            Optional Argument.
            Specifies queryband string.
            Types: str

        attr:
            Optional Argument.
            Specifies name of a class attribute whose value is to be used as
            queryband string.
            Types: str

        method:
            Optional Argument.
            Specifies name of a class method which returns string to be used as
            queryband string.
            Note:
                This method of class is expected to be a no-arg utility method and
                should return an expected queryband string for some processing done
                by a class/class method which needs to be tracked by queryband.
            Types: str

        arg_name:
            Optional Argument.
            Specifies name of an argument of a decorated function/method, whose value
            is to be used as queryband string.
            Types: str

        prefix:
            Optional Argument.
            Specifies prefix to be applied to queryband string.
            Types: str

        suffix:
            Optional Argument.
            Specifies suffix to be applied to queryband string.
            Types: str

    EXAMPLES:
        >>> from teradatasqlalchemy.telemetry import collect_queryband
        # Example 1: Collect queryband for a standalone function.
        @collect_queryband(session_queryband=QueryBand(), queryband="CreateContext")
        def create_context(host = None, username ...): ...

        # Example 2: Collect queryband for a class method and use
        #            class attribute to retrive queryband string.
        @collect_queryband(session_queryband=QueryBand(), attr="func_name")
        def _execute_query(self, persist=False, volatile=False):...

        # Example 3: Collect queryband for a class method and use
        #            method of same class to retrive queryband string.
        @collect_queryband(session_queryband=QueryBand(), method="get_class_specific_queryband")
        def _execute_query(self, persist=False, volatile=False):...
    """
    def qb_decorator(exposed_func):
        # This is needed to preserve the docstring of decorated function.
        @wraps(exposed_func)
        def wrapper(*args, **kwargs):
            qb_str = queryband
            # If queryband string is not provided by client while calling decorator,
            # it can be devised using following ways.
            if not qb_str:
                # Approach 1:
                # Extract queryband from value of argument passed
                # to decorated function/method.
                if arg_name:
                    # Extract value from Keyword arguments.
                    if arg_name in kwargs:
                        qb_str = kwargs[arg_name]

                    # Extract value from positional arguments.
                    # Also consider default values.
                    else:
                        # Generate a dictionary containing mapping between
                        # argument names and their run time values.
                        signature = inspect.signature(exposed_func)
                        bound_args = signature.bind(*args, **kwargs)
                        bound_args.apply_defaults()

                        qb_str = bound_args.arguments[arg_name]

                # Approach 2:
                # Extract queryband from an attribute/method associated
                # with class object.
                is_instance_method = args and ('.' in exposed_func.__qualname__)
                if is_instance_method:
                    try:
                        if attr:
                            qb_str = getattr(args[0], attr)
                        elif method:
                            qb_str = getattr(args[0], method)()
                    except Exception as stat_method_err:
                        session_queryband.log("Failed to collect queryband for static class method.", stat_method_err)
                        return exposed_func(*args, **kwargs)
                else:
                    session_queryband.log("Failed to collect queryband for standalone function.")
                    return exposed_func(*args, **kwargs)

            if qb_str:
                # Validate queryband for string type.
                if not isinstance(qb_str, str):
                    session_queryband.log("Failed to collect queryband. Queryband must be of type str not {}".format(type(qb_str)))
                    return exposed_func(*args, **kwargs)

                # Process suffix and prefix.
                if suffix and isinstance(suffix, str):
                    qb_str = qb_str + "_" + suffix
                if prefix and isinstance(prefix, str):
                    qb_str = prefix + "_" + qb_str

                # Validate queryband for allowed characters.
                if not re.match(session_queryband.qb_regex, qb_str):
                    session_queryband.log("Failed to collect queryband. Queryband string: '{}' contains invalid characters. Allowed characters are [a-z, A-Z, 0-9, '_', '-']".format(qb_str))
                    return exposed_func(*args, **kwargs)

                # Append queryband to buffer.
                session_queryband.append_qb(qb_str)

            return exposed_func(*args, **kwargs)

        return wrapper
    return qb_decorator


def set_queryband(session_queryband, con_obj):
    """
    DESCRIPTION:
        Decorator for executing set queryband SQL request using connection object from application
        and then clearing queryband buffer for next workflow.

    PARAMETERS:
        session_queryband:
            Required Argument.
            Specifies Queryband object to be used to set queryband.
            Types: Teradatasqlalchemy QueryBand

        con_obj:
            Required Argument.
            Specifies connection object to execute string.
            Types: Sqlalchemy connection


    EXAMPLES:
        Setting queryband before execution of application's SQL request.
        >>> from teradatasqlalchemy.telemetry import set_queryband
        @set_queryband(session_queryband=QueryBand(), con_obj=get_connection())
        def _execute_ddl_statement(ddl_statement):...
    """
    def qb_decorator(execute_func):
        def wrapper(*args, **kwargs):
            # Execute set queryband SQL request.
            try:
                session_queryband.execute_set_queryband(con_obj)
            except Exception as qb_err:
                session_queryband.log("Failed to set QB!!!", qb_err)
            # Execute application's SQL request and after successful execution
            # clean queryband buffer.
            try:
                ret_val = execute_func(*args, **kwargs)
            except Exception as exec_err:
                raise
            else:
                session_queryband.reset_qb()
            return ret_val
        return wrapper
    return qb_decorator
