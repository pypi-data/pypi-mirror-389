"""Register layout constants for Moncube Modbus facade."""

# Per-cubicle block size
BLOCK_SIZE = 512

# Shared hash lookup table (at the very beginning, before all cubicles)
SHARED_HASH_START = 1
SHARED_HASH_SIZE = 100  # 100 alarm slots

# Alarm region (flat, no bands/categories) - per cubicle
ALARM_REGION_START = 0  # Relative to cubicle base
ALARM_REGION_SIZE = 100  # 100 flat alarm slots (matches hash table)

# Meta region - per cubicle
META_REGION_START = ALARM_REGION_START + ALARM_REGION_SIZE  # 100
META_AGE_OFFSET = META_REGION_START + 0  # 100
META_QUALITY_OFFSET = META_REGION_START + 1  # 101
NEXT_AFTER_META = META_REGION_START + 16  # 116 - leave small headroom

# Data regions (fixed, 16 registers each)
DATA_REGION_SIZE = 16
DATA_TEMP_START = NEXT_AFTER_META  # 116
DATA_PD_START = DATA_TEMP_START + DATA_REGION_SIZE  # 132
DATA_ARC_START = DATA_PD_START + DATA_REGION_SIZE  # 148
DATA_HUM_START = DATA_ARC_START + DATA_REGION_SIZE  # 164

# Alarm severity domain
SEVERITY_MIN = 1  # Good
SEVERITY_MAX = 4  # Critical
# 1=Good, 2=Warning, 3=Alert, 4=Critical

# Data quality values
QUALITY_GOOD = 0
QUALITY_STALE = 1
QUALITY_BAD = 2
