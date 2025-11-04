from pyrogram import filters 
from ..moudels.admin.admin_manager import admin_filter
from ..moudels.account import (account_manager,account_viewer,cleaner)
from ..moudels.account.device import (device_manager)
from ..moudels.account.client import (client_manager)
from ..moudels.account.profile import (profile_info,profile_media,profile_privacy,username_manager)
from ..moudels.admin import (admin_manager)
from ..moudels.analytics import (analytics_manager)
from ..moudels.batch import (batch_manager,batch_scheduler)
from ..moudels.core import (config,restart_module,response_manager,getcode_controller,help_menu,precise_engine)
from ..moudels.db import (db_monitor,sqlite_utils)
from ..moudels.group import (join_controller,joiner,leave_controller,lefter)
from ..moudels.spammer import (spammer,speed_manager,stop_manager)
from ..moudels.text import (caption_manager,finaly_text,mention_manager,text_manager)
from ..moudels.utils import (block_manager,file_sender,health)

def register_commands(app): 

    # -------------------- Commands --------------------
    @app.on_message(admin_filter & filters.command("anti_login", prefixes=["/", ""]))
    async def cmd_anti_login(client, message):
        pass

    @app.on_message(admin_filter & filters.command("set_target_anti_login_sender", prefixes=["/", ""]))
    async def cmd_set_target_cmd(client, message):
        pass