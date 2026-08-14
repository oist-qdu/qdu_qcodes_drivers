import time

import numpy as np

from qcodes.instrument import VisaInstrument
from qcodes.parameters import ParameterWithSetpoints
from qcodes.validators import Arrays, Enum, Ints, Numbers


class AnritsuMS2025B(VisaInstrument):
    """
    QCoDeS driver for Anritsu MS2025B VNA Master.
    Author: QDUnit@mbelianchikov

    - Trace 1 only
    - S11 / S21
    - ASCII data transfer
    - Frequency axis read from the VNA
    - returns complex S-parameter data
    """

    MIN_FREQ = 500e3
    MAX_FREQ = 6e9

    VALID_IFBW = (
        10,
        20,
        50,
        100,
        200,
        500,
        1000,
        2000,
        5000,
        10000,
        20000,
        50000,
        100000,
    )

    SWEEP_COMPLETE_MASK = 256

    def __init__(
        self,
        name: str,
        address: str,
        *,
        timeout: float = 10.0,
        **kwargs,
    ):
        super().__init__(
            name=name,
            address=address,
            terminator="\n",
            **kwargs,
        )

        self.timeout(timeout)

        # The default PyVISA chunk size (~20 kB) is too small
        # for large ASCII traces from the MS2025B.
        self.visa_handle.chunk_size = 102400

        self.add_parameter(
            "start",
            label="Start frequency",
            unit="Hz",
            get_cmd=":SENS:FREQ:STAR?",
            set_cmd=":SENS:FREQ:STAR {:.12g}",
            get_parser=float,
            vals=Numbers(
                self.MIN_FREQ,
                self.MAX_FREQ,
            ),
        )

        self.add_parameter(
            "stop",
            label="Stop frequency",
            unit="Hz",
            get_cmd=":SENS:FREQ:STOP?",
            set_cmd=":SENS:FREQ:STOP {:.12g}",
            get_parser=float,
            vals=Numbers(
                self.MIN_FREQ,
                self.MAX_FREQ,
            ),
        )

        self.add_parameter(
            "center",
            label="Center frequency",
            unit="Hz",
            get_cmd=":SENS:FREQ:CENT?",
            set_cmd=":SENS:FREQ:CENT {:.12g}",
            get_parser=float,
            vals=Numbers(
                self.MIN_FREQ,
                self.MAX_FREQ,
            ),
        )

        self.add_parameter(
            "span",
            label="Frequency span",
            unit="Hz",
            get_cmd=":SENS:FREQ:SPAN?",
            set_cmd=":SENS:FREQ:SPAN {:.12g}",
            get_parser=float,
            vals=Numbers(
                0,
                self.MAX_FREQ - self.MIN_FREQ,
            ),
        )

        self.add_parameter(
            "points",
            label="Sweep points",
            get_cmd=":SENS:SWE:POIN?",
            set_cmd=":SENS:SWE:POIN {:d}",
            get_parser=lambda x: int(float(x)),
            vals=Ints(2, 4001),
        )

        self.add_parameter(
            "if_bandwidth",
            label="IF bandwidth",
            unit="Hz",
            get_cmd=":SENS:SWE:IFBW?",
            set_cmd=":SENS:SWE:IFBW {:d}",
            get_parser=lambda x: int(float(x)),
            set_parser=int,
            vals=Enum(*self.VALID_IFBW),
        )

        self.add_parameter(
            "s_parameter",
            label="S parameter",
            get_cmd=":SENS:TRAC1:SPAR?",
            set_cmd=":SENS:TRAC1:SPAR {}",
            get_parser=lambda x: x.strip().upper(),
            vals=Enum(
                "S11",
                "S21",
            ),
        )

        self.add_parameter(
            "source_power",
            label="Source power level",
            get_cmd=":SOUR:POW?",
            set_cmd=":SOUR:POW {}",
            get_parser=lambda x: x.strip().upper(),
            vals=Enum(
                "LOW",
                "DFLT",
                "HIGH",
            ),
        )

        self.add_parameter(
            "continuous",
            label="Continuous sweep",
            get_cmd=":INIT:CONT?",
            set_cmd=self._set_continuous,
            get_parser=lambda x: bool(int(x)),
            vals=Enum(
                True,
                False,
            ),
        )

        self.add_parameter(
            "freq_axis",
            label="Frequency",
            unit="Hz",
            get_cmd=self._get_frequencies,
            vals=Arrays(
                shape=(self.points,),
            ),
        )

        self.add_parameter(
            "complex",
            label="S parameter",
            unit="",
            parameter_class=ParameterWithSetpoints,
            setpoints=(
                self.freq_axis,
            ),
            get_cmd=self._get_trace,
            vals=Arrays(
                shape=(self.points,),
                valid_types=(np.complexfloating,),
            ),
        )


        # Trace data are transferred as ASCII.
        self.write(":FORM:DATA ASC")
        
        self.connect_message()

    def get_idn(self):
        """
        Query and parse *IDN?.
        """

        response = self.ask("*IDN?").strip()

        parts = [
            item.strip()
            for item in response.split(",")
        ]

        return {
            "vendor": parts[0] if len(parts) > 0 else None,
            "model": parts[1] if len(parts) > 1 else None,
            "serial": parts[2] if len(parts) > 2 else None,
            "firmware": parts[3] if len(parts) > 3 else None,
        }

    def _set_continuous(
        self,
        state: bool,
    ):
        """
        Enable or disable continuous sweep.
        """

        self.write(
            f":INIT:CONT {1 if state else 0}"
        )

    def trigger(self):
        """
        Trigger a new sweep.
        """

        self.write(":INIT:IMM")

    def get_operation_status(self) -> int:
        """
        Read the Operation Status Register.
        """

        return int(
            self.ask(":STAT:OPER?")
        )

    def sweep_complete(self) -> bool:
        """
        Check the sweep-complete bit.
        """

        status = self.get_operation_status()

        return bool(status & self.SWEEP_COMPLETE_MASK)

    def wait_for_sweep(
        self,
        timeout: float = 30.0,
        poll_interval: float = 0.05,
    ):
        """
        Wait for the current sweep to complete.
        """

        start_time = time.monotonic()

        while True:

            if self.sweep_complete():
                return

            if (
                time.monotonic()
                - start_time
                > timeout
            ):
                raise TimeoutError(
                    "MS2025B sweep did not finish "
                    f"within {timeout} s."
                )

            time.sleep(
                poll_interval
            )

    def single_sweep(
        self,
        timeout: float = 120.0,
    ):
        """
        Perform one synchronized sweep.
        """

        self.continuous(False)

        self.trigger()

        self.wait_for_sweep(
            timeout=timeout
        )

    # ================================================================
    # ASCII block parser
    # ================================================================

    @staticmethod
    def _parse_ascii_block(response: str,) -> np.ndarray:
        """
        Parse an IEEE 488.2 definite-length block containing
        comma-separated ASCII numeric values.

        Example:

            #60680175.0000000000E+05,...

        means:

            #       block marker
            6       six digits specify payload length
            068017  payload contains 68017 characters
        """

        response = response.strip()

        # Also accept ordinary comma-separated ASCII responses.
        if not response.startswith("#"):
            return np.fromstring(
                response,
                sep=",",
                dtype=float,
            )

        if len(response) < 2:
            raise RuntimeError(
                "Invalid IEEE block header."
            )

        n_digits = int(
            response[1]
        )

        if n_digits == 0:
            raise ValueError(
                "Indefinite-length IEEE blocks "
                "are not supported."
            )

        length_start = 2
        length_end = (
            length_start
            + n_digits
        )

        payload_length = int(
            response[
                length_start:length_end
            ]
        )

        payload_start = length_end
        payload_end = (
            payload_start
            + payload_length
        )

        payload = response[
            payload_start:payload_end
        ]

        if len(payload) != payload_length:

            raise RuntimeError(
                "Incomplete IEEE block: "
                f"expected {payload_length} characters, "
                f"received {len(payload)}."
            )

        return np.fromstring(
            payload,
            sep=",",
            dtype=float,
        )

    # ================================================================
    # Frequency-axis
    # ================================================================

    def _get_frequencies(self,) -> np.ndarray:
        """
        Read the actual frequency axis for Trace 1.
        """

        response = self.ask(
            ":SENS1:FREQ:DATA?"
        )

        frequencies = (
            self._parse_ascii_block(
                response
            )
        )

        return frequencies

    # ================================================================
    # Trace
    # ================================================================

    def _get_trace(self,) -> np.ndarray:

        self.single_sweep()

        response = self.ask(
            ":TRAC:DATA? 1"
        )

        values = (
            self._parse_ascii_block(
                response
            )
        )

        if values.size % 2:

            raise RuntimeError(
                "Trace contains an odd number "
                "of real/imaginary values. "
                f"Received {values.size} values."
            )

        real = values[0::2]
        imag = values[1::2]

        return (real + 1j * imag)