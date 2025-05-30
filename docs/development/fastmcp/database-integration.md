# Database Integration

Comprehensive guide to integrating databases with FastMCP servers, covering SQL and NoSQL databases, connection pooling, ORM patterns, and production-ready database management.

## Overview

FastMCP provides excellent database integration capabilities through its lifespan management system, dependency injection via Context, and support for all major Python async database libraries. This guide covers patterns for PostgreSQL, MySQL, SQLite, MongoDB, and Redis integration with best practices for production deployments.

## Database Lifecycle Management

### Basic Database Integration Pattern

FastMCP's lifespan management is perfect for database connections:

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP, Context
import asyncpg

@asynccontextmanager
async def database_lifespan(app: FastMCP):
    """Manage database connection lifecycle."""
    # Initialize database pool
    pool = await asyncpg.create_pool(
        "postgresql://user:password@localhost:5432/mydb",
        min_size=5,
        max_size=20,
        command_timeout=60
    )

    # Store pool in app for access in tools
    app.db_pool = pool

    try:
        yield {"db_pool": pool}
    finally:
        # Cleanup on shutdown
        await pool.close()

# Create FastMCP server with database lifespan
mcp = FastMCP("database-server", lifespan=database_lifespan)

@mcp.tool()
async def get_users(limit: int = 10, ctx: Context) -> list[dict]:
    """Get users from database."""
    async with mcp.db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, email FROM users LIMIT $1",
            limit
        )

        users = [dict(row) for row in rows]
        await ctx.info(f"Retrieved {len(users)} users")
        return users

if __name__ == "__main__":
    mcp.run("streamable-http")
```

## PostgreSQL Integration

### AsyncPG with Connection Pooling

AsyncPG provides high-performance PostgreSQL access with connection pooling:

```python
import asyncpg
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import os

class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int]

@asynccontextmanager
async def postgres_lifespan(app: FastMCP):
    """PostgreSQL connection management with schema setup."""
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/fastmcp"
    )

    # Create connection pool
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=60,
        server_settings={
            'application_name': 'fastmcp-server',
            'jit': 'off'  # Disable JIT for faster connection
        }
    )

    # Initialize database schema
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                age INTEGER CHECK (age >= 0 AND age <= 150),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
        """)

    app.db_pool = pool

    try:
        yield {"db_pool": pool}
    finally:
        await pool.close()

mcp = FastMCP("postgres-server", lifespan=postgres_lifespan)

@mcp.tool()
async def create_user(user_data: UserCreate, ctx: Context) -> UserResponse:
    """Create a new user with transaction safety."""
    async with mcp.db_pool.acquire() as conn:
        async with conn.transaction():
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO users (name, email, age)
                    VALUES ($1, $2, $3)
                    RETURNING id, name, email, age
                    """,
                    user_data.name, user_data.email, user_data.age
                )

                user = UserResponse(**dict(row))
                await ctx.info(f"Created user: {user.name} (ID: {user.id})")
                return user

            except asyncpg.UniqueViolationError:
                await ctx.error(f"Email {user_data.email} already exists")
                raise ValueError("Email already exists")
            except asyncpg.CheckViolationError as e:
                await ctx.error(f"Data validation failed: {e}")
                raise ValueError("Invalid user data")

@mcp.tool()
async def search_users(
    search_term: str,
    limit: int = 20,
    offset: int = 0,
    ctx: Context
) -> dict:
    """Search users with pagination."""
    async with mcp.db_pool.acquire() as conn:
        # Get total count
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE name ILIKE $1 OR email ILIKE $1",
            f"%{search_term}%"
        )

        # Get paginated results
        rows = await conn.fetch(
            """
            SELECT id, name, email, age, created_at
            FROM users
            WHERE name ILIKE $1 OR email ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            f"%{search_term}%", limit, offset
        )

        users = [dict(row) for row in rows]

        await ctx.info(f"Found {len(users)} users (total: {total})")

        return {
            "users": users,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(users) < total
            }
        }

@mcp.tool()
async def update_user(
    user_id: int,
    updates: dict,
    ctx: Context
) -> UserResponse:
    """Update user with dynamic fields."""
    allowed_fields = {"name", "email", "age"}
    update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

    if not update_fields:
        raise ValueError("No valid fields to update")

    # Build dynamic UPDATE query
    set_clauses = [f"{field} = ${i+2}" for i, field in enumerate(update_fields.keys())]
    query = f"""
        UPDATE users
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = $1
        RETURNING id, name, email, age
    """

    async with mcp.db_pool.acquire() as conn:
        async with conn.transaction():
            try:
                row = await conn.fetchrow(query, user_id, *update_fields.values())

                if not row:
                    raise ValueError(f"User {user_id} not found")

                user = UserResponse(**dict(row))
                await ctx.info(f"Updated user {user_id}: {list(update_fields.keys())}")
                return user

            except asyncpg.UniqueViolationError:
                await ctx.error(f"Email conflict during update")
                raise ValueError("Email already exists")

@mcp.tool()
async def delete_user(user_id: int, ctx: Context) -> dict:
    """Delete user with soft delete option."""
    async with mcp.db_pool.acquire() as conn:
        # Check if user exists first
        user = await conn.fetchrow("SELECT name FROM users WHERE id = $1", user_id)

        if not user:
            await ctx.warning(f"User {user_id} not found")
            return {"success": False, "message": "User not found"}

        # Delete user
        result = await conn.execute("DELETE FROM users WHERE id = $1", user_id)

        if result == "DELETE 1":
            await ctx.info(f"Deleted user {user_id} ({user['name']})")
            return {"success": True, "message": f"User {user['name']} deleted"}
        else:
            return {"success": False, "message": "Delete failed"}
```

### SQLAlchemy ORM Integration

For complex applications requiring ORM features:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, select, update, delete
from datetime import datetime
from typing import List

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationship to posts
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationship to user
    author: Mapped["User"] = relationship("User", back_populates="posts")

@asynccontextmanager
async def sqlalchemy_lifespan(app: FastMCP):
    """SQLAlchemy async engine and session management."""
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/fastmcp"
    )

    # Create async engine
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Validate connections
        echo=os.getenv("DEBUG") == "true"  # SQL logging in debug mode
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    app.async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        yield {"engine": engine}
    finally:
        await engine.dispose()

mcp = FastMCP("sqlalchemy-server", lifespan=sqlalchemy_lifespan)

@mcp.tool()
async def create_user_with_posts(
    name: str,
    email: str,
    posts: List[dict],
    ctx: Context
) -> dict:
    """Create user with initial posts using SQLAlchemy ORM."""
    async with mcp.async_session() as session:
        async with session.begin():
            try:
                # Create user
                user = User(name=name, email=email)
                session.add(user)
                await session.flush()  # Get user ID

                # Create posts
                post_objects = []
                for post_data in posts:
                    post = Post(
                        title=post_data["title"],
                        content=post_data["content"],
                        author_id=user.id
                    )
                    session.add(post)
                    post_objects.append(post)

                await session.commit()

                await ctx.info(f"Created user {name} with {len(posts)} posts")

                return {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "created_at": user.created_at.isoformat()
                    },
                    "posts_created": len(posts)
                }

            except Exception as e:
                await session.rollback()
                await ctx.error(f"Failed to create user: {e}")
                raise

@mcp.tool()
async def get_user_with_posts(user_id: int, ctx: Context) -> dict:
    """Get user with their posts using eager loading."""
    async with mcp.async_session() as session:
        # Eager load posts with user
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.posts))
        )

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await ctx.warning(f"User {user_id} not found")
            return {"error": "User not found"}

        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "posts": [
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "created_at": post.created_at.isoformat()
                }
                for post in user.posts
            ]
        }

        await ctx.info(f"Retrieved user {user.name} with {len(user.posts)} posts")
        return user_data

@mcp.tool()
async def bulk_update_posts(
    author_id: int,
    updates: dict,
    ctx: Context
) -> dict:
    """Bulk update posts for an author."""
    async with mcp.async_session() as session:
        async with session.begin():
            # Update all posts by author
            stmt = (
                update(Post)
                .where(Post.author_id == author_id)
                .values(**updates)
                .returning(Post.id)
            )

            result = await session.execute(stmt)
            updated_ids = [row[0] for row in result.fetchall()]

            await ctx.info(f"Updated {len(updated_ids)} posts for author {author_id}")

            return {
                "updated_count": len(updated_ids),
                "updated_post_ids": updated_ids,
                "updates_applied": updates
            }
```

## MySQL Integration

### aiomysql with Connection Pooling

```python
import aiomysql
from contextlib import asynccontextmanager

@asynccontextmanager
async def mysql_lifespan(app: FastMCP):
    """MySQL connection pool management."""
    pool = await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='mysql_user',
        password='mysql_password',
        db='fastmcp_db',
        minsize=5,
        maxsize=20,
        charset='utf8mb4',
        autocommit=False
    )

    # Initialize schema
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    category VARCHAR(100),
                    in_stock BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_price (price)
                ) ENGINE=InnoDB
            """)
            await conn.commit()

    app.mysql_pool = pool

    try:
        yield {"mysql_pool": pool}
    finally:
        pool.close()
        await pool.wait_closed()

mcp = FastMCP("mysql-server", lifespan=mysql_lifespan)

@mcp.tool()
async def add_product(
    name: str,
    price: float,
    category: str,
    in_stock: bool = True,
    ctx: Context
) -> dict:
    """Add product to MySQL database."""
    async with mcp.mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute(
                    """
                    INSERT INTO products (name, price, category, in_stock)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (name, price, category, in_stock)
                )

                product_id = cursor.lastrowid
                await conn.commit()

                await ctx.info(f"Added product: {name} (ID: {product_id})")

                return {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "category": category,
                    "in_stock": in_stock
                }

            except Exception as e:
                await conn.rollback()
                await ctx.error(f"Failed to add product: {e}")
                raise

@mcp.tool()
async def search_products(
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    in_stock_only: bool = True,
    ctx: Context
) -> list[dict]:
    """Search products with filters."""
    async with mcp.mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Build dynamic query
            conditions = []
            params = []

            if category:
                conditions.append("category = %s")
                params.append(category)

            if min_price is not None:
                conditions.append("price >= %s")
                params.append(min_price)

            if max_price is not None:
                conditions.append("price <= %s")
                params.append(max_price)

            if in_stock_only:
                conditions.append("in_stock = TRUE")

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
                SELECT id, name, price, category, in_stock, created_at
                FROM products
                {where_clause}
                ORDER BY created_at DESC
                LIMIT 100
            """

            await cursor.execute(query, params)
            products = await cursor.fetchall()

            await ctx.info(f"Found {len(products)} products")
            return products
```

## SQLite Integration

Lightweight database perfect for development and small applications:

```python
import aiosqlite
from pathlib import Path

@asynccontextmanager
async def sqlite_lifespan(app: FastMCP):
    """SQLite database management."""
    db_path = Path("fastmcp.db")

    # Connect to SQLite
    conn = await aiosqlite.connect(str(db_path))

    # Enable foreign keys and WAL mode
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.execute("PRAGMA journal_mode = WAL")

    # Create schema
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
    """)

    await conn.commit()
    app.sqlite_conn = conn

    try:
        yield {"sqlite_conn": conn}
    finally:
        await conn.close()

mcp = FastMCP("sqlite-server", lifespan=sqlite_lifespan)

@mcp.tool()
async def create_task(
    title: str,
    description: str = "",
    priority: int = 1,
    ctx: Context
) -> dict:
    """Create a new task."""
    async with mcp.sqlite_conn.execute(
        """
        INSERT INTO tasks (title, description, priority)
        VALUES (?, ?, ?)
        """,
        (title, description, priority)
    ) as cursor:
        task_id = cursor.lastrowid

    await mcp.sqlite_conn.commit()

    await ctx.info(f"Created task: {title} (ID: {task_id})")

    return {
        "id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending"
    }

@mcp.tool()
async def get_tasks(
    status: str = None,
    priority: int = None,
    limit: int = 50,
    ctx: Context
) -> list[dict]:
    """Get tasks with optional filtering."""
    query = "SELECT * FROM tasks"
    params = []
    conditions = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if priority:
        conditions.append("priority = ?")
        params.append(priority)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
    params.append(limit)

    async with mcp.sqlite_conn.execute(query, params) as cursor:
        rows = await cursor.fetchall()

        # Convert rows to dictionaries
        columns = [description[0] for description in cursor.description]
        tasks = [dict(zip(columns, row)) for row in rows]

    await ctx.info(f"Retrieved {len(tasks)} tasks")
    return tasks
```

## NoSQL Database Integration

### MongoDB with Motor

```python
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

@asynccontextmanager
async def mongodb_lifespan(app: FastMCP):
    """MongoDB connection management."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.fastmcp_db

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("created_at")
    await db.posts.create_index([("author_id", 1), ("created_at", -1)])

    app.mongodb = db

    try:
        yield {"mongodb": db}
    finally:
        client.close()

mcp = FastMCP("mongodb-server", lifespan=mongodb_lifespan)

@mcp.tool()
async def create_user_mongo(
    name: str,
    email: str,
    metadata: dict = None,
    ctx: Context
) -> dict:
    """Create user in MongoDB."""
    user_doc = {
        "name": name,
        "email": email,
        "created_at": datetime.utcnow(),
        "metadata": metadata or {}
    }

    try:
        result = await mcp.mongodb.users.insert_one(user_doc)

        await ctx.info(f"Created MongoDB user: {name}")

        return {
            "id": str(result.inserted_id),
            "name": name,
            "email": email,
            "created_at": user_doc["created_at"].isoformat()
        }

    except Exception as e:
        await ctx.error(f"Failed to create user: {e}")
        raise

@mcp.tool()
async def find_users_mongo(
    query: dict = None,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: int = -1,
    ctx: Context
) -> list[dict]:
    """Find users in MongoDB with flexible querying."""
    query = query or {}

    cursor = (
        mcp.mongodb.users
        .find(query)
        .sort(sort_by, sort_order)
        .limit(limit)
    )

    users = []
    async for doc in cursor:
        doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
        if 'created_at' in doc:
            doc['created_at'] = doc['created_at'].isoformat()
        users.append(doc)

    await ctx.info(f"Found {len(users)} users matching query")
    return users

@mcp.tool()
async def aggregate_user_stats(ctx: Context) -> dict:
    """Get user statistics using MongoDB aggregation."""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_users": {"$sum": 1},
                "avg_metadata_fields": {"$avg": {"$size": {"$objectToArray": "$metadata"}}},
                "oldest_user": {"$min": "$created_at"},
                "newest_user": {"$max": "$created_at"}
            }
        }
    ]

    async for result in mcp.mongodb.users.aggregate(pipeline):
        stats = {
            "total_users": result["total_users"],
            "avg_metadata_fields": result["avg_metadata_fields"],
            "oldest_user": result["oldest_user"].isoformat() if result["oldest_user"] else None,
            "newest_user": result["newest_user"].isoformat() if result["newest_user"] else None
        }

        await ctx.info(f"Generated user statistics: {stats['total_users']} total users")
        return stats

    return {"total_users": 0}
```

### Redis Integration

For caching and session storage:

```python
import redis.asyncio as redis
import json
from typing import Any

@asynccontextmanager
async def redis_lifespan(app: FastMCP):
    """Redis connection management."""
    redis_client = redis.from_url("redis://localhost:6379")

    # Test connection
    await redis_client.ping()

    app.redis = redis_client

    try:
        yield {"redis": redis_client}
    finally:
        await redis_client.close()

mcp = FastMCP("redis-server", lifespan=redis_lifespan)

@mcp.tool()
async def cache_data(
    key: str,
    data: Any,
    ttl: int = 3600,
    ctx: Context
) -> dict:
    """Cache data in Redis with TTL."""
    serialized_data = json.dumps(data)

    await mcp.redis.setex(key, ttl, serialized_data)

    await ctx.info(f"Cached data with key: {key} (TTL: {ttl}s)")

    return {
        "key": key,
        "ttl": ttl,
        "data_size": len(serialized_data)
    }

@mcp.tool()
async def get_cached_data(key: str, ctx: Context) -> dict:
    """Retrieve cached data from Redis."""
    data = await mcp.redis.get(key)

    if data is None:
        await ctx.warning(f"Cache miss for key: {key}")
        return {"found": False, "key": key}

    # Get TTL
    ttl = await mcp.redis.ttl(key)

    try:
        parsed_data = json.loads(data)
        await ctx.info(f"Cache hit for key: {key}")

        return {
            "found": True,
            "key": key,
            "data": parsed_data,
            "ttl_remaining": ttl
        }
    except json.JSONDecodeError:
        await ctx.error(f"Failed to parse cached data for key: {key}")
        return {"found": False, "key": key, "error": "Parse error"}

@mcp.tool()
async def redis_stats(ctx: Context) -> dict:
    """Get Redis server statistics."""
    info = await mcp.redis.info()

    stats = {
        "redis_version": info.get("redis_version"),
        "used_memory": info.get("used_memory"),
        "used_memory_human": info.get("used_memory_human"),
        "connected_clients": info.get("connected_clients"),
        "total_commands_processed": info.get("total_commands_processed"),
        "keyspace": {}
    }

    # Get keyspace info
    for key, value in info.items():
        if key.startswith("db"):
            stats["keyspace"][key] = value

    await ctx.info("Retrieved Redis statistics")
    return stats
```

## Database Configuration Management

### Environment-Based Configuration

```python
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class DatabaseSettings(BaseSettings):
    """Type-safe database configuration."""
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        secrets_dir="/run/secrets"
    )

    # Database connection
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")
    name: str = Field(..., description="Database name")

    # Connection pool settings
    min_pool_size: int = Field(default=5, ge=1, le=50)
    max_pool_size: int = Field(default=20, ge=1, le=100)
    pool_timeout: int = Field(default=60, ge=1, le=300)

    # SSL settings
    ssl_mode: Literal["disable", "require", "verify-ca", "verify-full"] = "disable"
    ssl_cert: str = None
    ssl_key: str = None
    ssl_ca: str = None

    @validator('max_pool_size')
    def validate_pool_sizes(cls, v, values):
        min_size = values.get('min_pool_size', 5)
        if v < min_size:
            raise ValueError('max_pool_size must be >= min_pool_size')
        return v

    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def ssl_context(self):
        """Generate SSL context if needed."""
        if self.ssl_mode == "disable":
            return None

        import ssl
        context = ssl.create_default_context()

        if self.ssl_mode == "require":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif self.ssl_ca:
            context.load_verify_locations(self.ssl_ca)

        if self.ssl_cert and self.ssl_key:
            context.load_cert_chain(self.ssl_cert, self.ssl_key)

        return context

# Usage
db_settings = DatabaseSettings()

@asynccontextmanager
async def configured_database_lifespan(app: FastMCP):
    """Database lifespan with configuration."""
    pool = await asyncpg.create_pool(
        db_settings.url,
        min_size=db_settings.min_pool_size,
        max_size=db_settings.max_pool_size,
        command_timeout=db_settings.pool_timeout,
        ssl=db_settings.ssl_context
    )

    app.db_pool = pool
    app.db_settings = db_settings

    try:
        yield {"db_pool": pool, "settings": db_settings}
    finally:
        await pool.close()
```

## Testing Database Tools

### Pytest with Database Fixtures

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import asyncpg

@pytest_asyncio.fixture
async def mock_db_pool():
    """Mock database pool for testing."""
    pool = AsyncMock()
    connection = AsyncMock()

    # Configure mock connection
    pool.acquire.return_value.__aenter__.return_value = connection
    connection.fetchrow.return_value = {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com"
    }
    connection.fetch.return_value = [
        {"id": 1, "name": "User 1"},
        {"id": 2, "name": "User 2"}
    ]
    connection.execute.return_value = "INSERT 0 1"

    return pool

@pytest_asyncio.fixture
async def test_mcp_app(mock_db_pool):
    """FastMCP app with mocked database."""
    app = FastMCP("test-server")
    app.db_pool = mock_db_pool
    return app

@pytest.mark.asyncio
async def test_create_user(test_mcp_app, mock_db_pool):
    """Test user creation with mocked database."""
    from mcp.server.fastmcp import Context

    # Mock context
    ctx = AsyncMock(spec=Context)

    # Test user creation
    user_data = UserCreate(name="John Doe", email="john@example.com")
    result = await create_user(user_data, ctx)

    # Verify database was called
    mock_db_pool.acquire.assert_called_once()

    # Verify result
    assert result.name == "John Doe"
    assert result.email == "john@example.com"

    # Verify logging
    ctx.info.assert_called()

@pytest_asyncio.fixture
async def test_database():
    """Real database fixture for integration tests."""
    # Create test database
    pool = await asyncpg.create_pool("postgresql://test:test@localhost:5432/test_db")

    # Setup test schema
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100) UNIQUE
            )
        """)

    try:
        yield pool
    finally:
        # Cleanup
        async with pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS test_users")
        await pool.close()

@pytest.mark.asyncio
async def test_integration_create_user(test_database):
    """Integration test with real database."""
    app = FastMCP("integration-test")
    app.db_pool = test_database

    ctx = AsyncMock(spec=Context)
    user_data = UserCreate(name="Integration User", email="integration@test.com")

    result = await create_user(user_data, ctx)

    # Verify in database
    async with test_database.acquire() as conn:
        db_user = await conn.fetchrow(
            "SELECT * FROM test_users WHERE email = $1",
            "integration@test.com"
        )

        assert db_user is not None
        assert db_user["name"] == "Integration User"
```

## Production Best Practices

### Connection Monitoring and Health Checks

```python
@mcp.custom_route("/health/database", methods=["GET"])
async def database_health_check(request) -> JSONResponse:
    """Database health check endpoint."""
    try:
        # Test database connectivity
        async with mcp.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        # Get pool statistics
        pool_stats = {
            "size": mcp.db_pool.get_size(),
            "idle_connections": mcp.db_pool.get_idle_size(),
            "max_size": mcp.db_pool._maxsize,
            "min_size": mcp.db_pool._minsize
        }

        return JSONResponse({
            "status": "healthy",
            "database": "connected",
            "pool_stats": pool_stats,
            "timestamp": time.time()
        })

    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": time.time()
        }, status_code=503)

@mcp.tool()
async def database_diagnostics(ctx: Context) -> dict:
    """Get detailed database diagnostics."""
    diagnostics = {}

    try:
        async with mcp.db_pool.acquire() as conn:
            # Database version
            version = await conn.fetchval("SELECT version()")
            diagnostics["database_version"] = version

            # Connection info
            diagnostics["connection_info"] = {
                "host": conn.get_dsn_parameters().get("host"),
                "port": conn.get_dsn_parameters().get("port"),
                "database": conn.get_dsn_parameters().get("dbname"),
                "user": conn.get_dsn_parameters().get("user")
            }

            # Performance metrics
            metrics = await conn.fetch("""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables
                ORDER BY schemaname, tablename
            """)

            diagnostics["table_stats"] = [dict(row) for row in metrics]

    except Exception as e:
        diagnostics["error"] = str(e)

    # Pool diagnostics
    diagnostics["pool_stats"] = {
        "size": mcp.db_pool.get_size(),
        "idle": mcp.db_pool.get_idle_size(),
        "max_size": mcp.db_pool._maxsize,
        "min_size": mcp.db_pool._minsize
    }

    await ctx.info("Generated database diagnostics")
    return diagnostics
```

### Performance Optimization

```python
from functools import lru_cache
import time

# Query caching
@lru_cache(maxsize=128)
def get_cached_query_result(query_hash: str, cache_time: int):
    """Cache query results based on time intervals."""
    # Cache for 5-minute intervals
    interval = cache_time // 300
    return f"cached_result_{query_hash}_{interval}"

@mcp.tool()
async def optimized_search(
    search_term: str,
    use_cache: bool = True,
    ctx: Context
) -> list[dict]:
    """Search with intelligent caching."""

    if use_cache:
        cache_key = f"search_{hash(search_term)}"
        cache_time = int(time.time())

        # Try cache first
        try:
            cached_result = get_cached_query_result(cache_key, cache_time)
            if cached_result:
                await ctx.info("Using cached search results")
                return cached_result
        except:
            pass

    # Execute database query
    async with mcp.db_pool.acquire() as conn:
        # Use prepared statement for performance
        stmt = await conn.prepare("""
            SELECT id, name, email, ts_rank(search_vector, query) as rank
            FROM users, plainto_tsquery($1) query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 50
        """)

        rows = await stmt.fetch(search_term)
        results = [dict(row) for row in rows]

    await ctx.info(f"Database search returned {len(results)} results")
    return results

# Batch operations for better performance
@mcp.tool()
async def batch_insert_users(
    users: list[dict],
    batch_size: int = 100,
    ctx: Context
) -> dict:
    """Insert users in batches for better performance."""
    total_inserted = 0

    async with mcp.db_pool.acquire() as conn:
        async with conn.transaction():
            # Process in batches
            for i in range(0, len(users), batch_size):
                batch = users[i:i + batch_size]

                # Prepare batch insert
                values = [(user["name"], user["email"]) for user in batch]

                await conn.executemany(
                    "INSERT INTO users (name, email) VALUES ($1, $2)",
                    values
                )

                total_inserted += len(batch)

                # Report progress
                await ctx.report_progress(
                    progress=total_inserted / len(users),
                    total=1.0,
                    message=f"Inserted {total_inserted} of {len(users)} users"
                )

    await ctx.info(f"Batch inserted {total_inserted} users")
    return {
        "total_inserted": total_inserted,
        "batch_size": batch_size,
        "batches_processed": (len(users) + batch_size - 1) // batch_size
    }
```

## Security Best Practices

### SQL Injection Prevention

```python
# ✅ SAFE: Always use parameterized queries
@mcp.tool()
async def safe_user_search(search_term: str, ctx: Context) -> list[dict]:
    """Safe user search with parameterized query."""
    async with mcp.db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM users WHERE name ILIKE $1 OR email ILIKE $1",
            f"%{search_term}%"
        )
        return [dict(row) for row in rows]

# ❌ UNSAFE: Never use string formatting
async def unsafe_search(search_term: str):
    query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"  # DON'T DO THIS
    # This is vulnerable to SQL injection attacks
```

### Access Control and Permissions

```python
from mcp.server.auth.middleware import get_access_token

@mcp.tool()
async def admin_database_operation(
    operation: str,
    ctx: Context
) -> dict:
    """Database operation requiring admin privileges."""
    # Check authentication and authorization
    access_token = get_access_token()

    if not access_token:
        raise ValueError("Authentication required")

    if "admin" not in access_token.scopes:
        raise ValueError("Admin privileges required")

    # Proceed with admin operation
    async with mcp.db_pool.acquire() as conn:
        if operation == "vacuum":
            await conn.execute("VACUUM ANALYZE")
            await ctx.info("Database vacuum completed")
            return {"operation": "vacuum", "status": "completed"}

        elif operation == "reindex":
            await conn.execute("REINDEX DATABASE")
            await ctx.info("Database reindex completed")
            return {"operation": "reindex", "status": "completed"}

        else:
            raise ValueError(f"Unknown admin operation: {operation}")
```

This comprehensive guide provides everything needed to integrate databases effectively with FastMCP servers, from basic connection management to production-ready patterns with security, monitoring, and optimization.
