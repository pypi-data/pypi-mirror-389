from itchi.config import ItchiConfig
from itchi.profilerxml.model import ProfilerXml


def arti(profiler_xml: ProfilerXml, config: ItchiConfig):
    """ARTI state profiling for Vector MICROSAR Timing Hooks.

    Args:
        profiler_xml (ProfilerXml): Profiler XML object
        config (ItchiConfig): iTCHi Config object
    """
    raise NotImplementedError(
        "iTCHi does not support ARTI. Import ARTI ARXML directly into winIDEA."
    )
