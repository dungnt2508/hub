
import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from sqlalchemy import select, desc
from app.infrastructure.database.engine import get_session_maker
from app.infrastructure.database.models import Tenant, Bot, BotVersion, RuntimeSession
from app.application.orchestrators.agent_orchestrator import AgentOrchestrator
from app.core.domain.runtime import LifecycleState

async def main():
    # Configuration
    TENANT_CODE = "anycar"
    BOT_CODE = None
    if len(sys.argv) > 1:
        TENANT_CODE = sys.argv[1]
    if len(sys.argv) > 2:
        BOT_CODE = sys.argv[2]
        
    print(f"--- Agent Orchestrator CLI Test ---")
    print(f"Target Tenant: {TENANT_CODE}")
    if BOT_CODE:
        print(f"Target Bot: {BOT_CODE}")
    
    session_maker = get_session_maker()
    
    async with session_maker() as db:
        # 1. Get Tenant
        res = await db.execute(select(Tenant).where(Tenant.name.ilike(f"%{TENANT_CODE}%")))
        tenant = res.scalars().first()
        if not tenant:
            print(f"Error: Tenant '{TENANT_CODE}' not found.")
            return
            
        print(f"Tenant ID: {tenant.id}")
        
        # 2. Get Bot
        bot_stmt = select(Bot).where(Bot.tenant_id == tenant.id)
        if BOT_CODE:
            bot_stmt = bot_stmt.where(Bot.code.ilike(f"%{BOT_CODE}%"))
            
        res = await db.execute(bot_stmt)
        bot = res.scalars().first()
        if not bot:
            msg = f"Error: No bot found for tenant '{tenant.name}'"
            if BOT_CODE: msg += f" matching code '{BOT_CODE}'"
            print(msg)
            return
            
        print(f"Bot Selected: {bot.name} ({bot.code})")
        print(f"Capabilities: {bot.capabilities}")
        
        # 3. Create/Get Session
        # Get latest bot version
        res = await db.execute(
            select(BotVersion)
            .where(BotVersion.bot_id == bot.id)
            .order_by(desc(BotVersion.version))
            .limit(1)
        )
        bot_version = res.scalar_one_or_none()
        if not bot_version:
            print(f"Error: No version found for bot '{bot.name}'")
            return
            
        # Create a fresh session for testing
        session_id = str(uuid.uuid4())
        db_session = RuntimeSession(
            id=session_id,
            tenant_id=tenant.id,
            bot_id=bot.id,
            bot_version_id=bot_version.id,
            channel_code="webchat",
            flow_step="START",
            ext_metadata={"user_id": "test-user-cli"}
        )
        db.add(db_session)
        await db.commit()
        print(f"Created Test Session: {session_id} (Version: {bot_version.version})")
        
        # 4. Initialize Orchestrator
        orchestrator = AgentOrchestrator(db)
        state_code = LifecycleState.IDLE
        
        print("\n--- Ready to Chat (Type 'exit' to quit) ---")
        
        while True:
            user_input = input("\nUser: ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            print("Agent is thinking...")
            try:
                result = await orchestrator.run(
                    message=user_input,
                    session_id=session_id,
                    state_code=state_code,
                    tenant_id=tenant.id
                )
                
                print(f"[Bot Response]: {result.get('response')}")
                
                # Update mock state (in real app, this is handled by state machine service)
                if result.get("new_state"):
                    state_code = result["new_state"]
                    print(f"[(State Transition) -> {state_code}]")
                    
                if result.get("g_ui_data"):
                    print(f"[UI Data]: {result['g_ui_data']['type']}")
                    
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
