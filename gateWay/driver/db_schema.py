import sqlalchemy as sa

# Define a version number for the database generated by these writers
# Increment this version number any time a change is made to the schema of the
# assets database
# NOTE: When upgrading this remember to add a downgrade in:
# .asset_db_migrations
ASSET_DB_VERSION = 7
# A frozenset of the names of all tables in the assets db
# NOTE: When modifying this schema, update the ASSET_DB_VERSION value
asset_db_table_names = frozenset({
    'symbol_naive_price',
    'dual_symbol_price'
    'bond_price',
    'index_price',
    'fund_price',
    'symbol_equity_basics',
    'bond_basics',
    'symbol_splits',
    'symbol_issue',
    'symbol_mcap',
    'symbol_massive',
    'market_margin',
    'version_info',
})

metadata = sa.MetaData()

engine = sa.create_engine('mysql+pymysql://root:macpython@localhost:3306/spider')
# autoincrement
symbol_basics = sa.Table(
    'symbol_basics',
    metadata,
    sa.Column(
        'sid',
        sa.String(10),
        unique=True,
        nullable=False,
        primary_key=True,
        index = True,
    ),
    sa.Column('ipo_date',sa.String(10)),
    sa.Column('ipo_price', sa.Numeric(10,2)),
    sa.Column('symbol_id', sa.Text),
    sa.Column('broker', sa.Text),
    sa.Column('area', sa.Text),
)

symbol_price = sa.Table(
    'symbol_naive_price',
    metadata,
    sa.Column('trade_dt',
            sa.String(10),
            nullable=False,
            primary_key=True,
    ),
    sa.Column(
        'sid',
        sa.String(10),
        sa.ForeignKey(symbol_basics.c.sid),
        nullable = False,
        primary_key=True,
    ),
    sa.Columns('open',sa.Numeric(10,2),nullable = False),
    sa.Columns('high', sa.Numeric(10, 2), nullable=False),
    sa.Columns('low', sa.Numeric(10, 2), nullable=False),
    sa.Columns('close', sa.Numeric(10, 2), nullable=False),
    sa.Column('turnover', sa.Numeric(10, 2),nullable = False),
    sa.Columns('volume', sa.Numeric(20,0), nullable=False),
    sa.Columns('amount', sa.Numeric(20, 2), nullable=False),
)

dual_symbol_price = sa.Table(
    'dual_symbol_price',
    metadata,
    sa.Column(
        'sid',
        sa.String(10),
        sa.ForeignKey(symbol_price.c.sid),
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        'sid_hk',
        sa.String(10),
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column('trade_dt', sa.String(10)),
    sa.Column('open', sa.Numeric(10,2)),
    sa.Column('high', sa.Numeric(10,2)),
    sa.Column('low', sa.Numeric(10,2)),
    sa.Column('close', sa.Numeric(10,2)),
    sa.Column('volume', sa.Numeric(20,0)),
)

bond_basics = sa.Table(
    'bond_basics',
    metadata,
    sa.Column(
        'bond_id',
        sa.String(10),
        unique= True,
        nullable = False,
        primary_key= True,
        index = True,
    ),
    sa.Column(
        'stock_id',
        sa.String(10),
        nullable = False,
    ),
    sa.Column('put_price',sa.Numeric(10,3)),
    sa.Column('convert_price', sa.Numeric(10, 2)),
    sa.Column('convert_dt', sa.String(10)),
    sa.Column('maturity_dt', sa.String(10)),
    sa.Column('force_redeem_price', sa.Numeric(10, 2)),
    sa.Column('put_convert_price', sa.Numeric(10, 2)),
    sa.Column('guarantor', sa.Text),
)


bond_price = sa.Table(
    'bond_price',
    metadata,
    sa.Column(
        'bond_id',
        sa.String(10),
        sa.ForeignKey(bond_basics.c.bond_id),
        nullable=False,
        primary_key=True,
    ),
    sa.Column('open',sa.String(10,2)),
    sa.Column('high', sa.String(10, 2)),
    sa.Column('low', sa.String(10, 2)),
    sa.Column('close', sa.String(10, 2)),
    sa.Column('volume', sa.String(20, 0)),
    sa.Column('amount', sa.String(20, 2)),
)

index_price = sa.Table(
    'index_price',
    metadata,
    sa.Column(
        'id',
        sa.Integer,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column('sid',sa.String(10)),
    sa.Column('cname',sa.Text),
    sa.Column('open', sa.Numeric(10,2)),
    sa.Column('high', sa.Numeric10,2),
    sa.Column('low', sa.Numeric(10,2)),
    sa.Column('close', sa.Numeric(10,2)),
    sa.Column('turnover', sa.Numeric(10, 2)),
    sa.Column('volume', sa.Numeric(10,2)),
    sa.Column('amount', sa.Numeric(10,2)),
)


fund_price = sa.Table(
    'fund_price',
    metadata,
    sa.Column(
        'id',
        sa.Integer,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column('sid',
        sa.String(10),
        nullable=False,
        index=True,
    ),
    sa.Column('trade_dt',sa.String(10),nullable=False),
    sa.Column('open', sa.Numeric(10,2), nullable=False),
    sa.Column('high', sa.Numeric(10,2), nullable=False),
    sa.Column('low', sa.Numeric(10,2), nullable=False),
    sa.Column('close', sa.Numeric(10,2), nullable=False),
    sa.Column('volume', sa.Numeric(10,0), nullable=False),
    sa.Column('amount', sa.Numeric(20,2), nullable=False),
)


# declared_date : 公告日期 ; record_date : 登记日 ; pay_date : 除权除息日
#红股上市日指上市公司所送红股可上市交易（卖出）的日期。上交所证券的红股上市日为股权除权日的下一个交易日；深交所证券的红股上市日为股权登记日后的第3个交易日。
symbol_splits = sa.Table(
    'symbol_splits',
    metadata,
    sa.Column(
        'sid',
        sa.String(10),
        sa.ForeignKey(symbol_price.c.sid),
        nullable=False,
        primary_key=True,
    ),
    sa.Column('declared_date', sa.String(10), primary_key =True),
    sa.Column('record_date',sa.String),
    sa.Column('pay_date',sa.String),
    sa.Column('payment_sid_bonus',sa.Integer),
    sa.Column('payment_sid_transfer', sa.Integer),
    sa.Column('payment_cash',sa.Numeric(5,2)),
    sa.Column('progress',sa.Text),
)

symbol_rights = sa.Table(
    'symbol_rights',
    metadata,
    sa.Column(
        'sid',
        sa.Integer,
        sa.ForeignKey(symbol_price.c.sid),
        nullable=False,
        primary_key=True,
    ),
    sa.Column('declared_date', sa.String(10), primary_key=True),
    sa.Column('record_date', sa.String(10)),
    sa.Column('pay_date', sa.String(10)),
    sa.Column('on_date',sa.String(10)),
    sa.Column('rights_bonus', sa.Integer),
    sa.Column('rights_price', sa.Numeric(5, 2)),
)

symbol_equity_basics = sa.Table(
    'symbol_equity_basics',
    metadata,
    sa.Column(
        'sid',
        sa.String(10),
        sa.ForeignKey(symbol_price.c.sid),
        nullable=False,
    ),
    sa.Column('declared_date', sa.String(10)),
    sa.Column('change_date', sa.String(10)),
    sa.Column('general_share', sa.Numeric(15,5)),
    sa.Column('float_ashare', sa.Numeric(15,5)),
    sa.Column('strict_ashare', sa.Numeric(15,5)),
    sa.Column('float_bshare', sa.Numeric(15,5)),
    sa.Column('strict_bshare', sa.Numeric(15,5)),
    sa.Column('float_hshare', sa.Numeric(15,5)),
)

symbol_mcap = sa.Table(
    'symbol_mcap',
    metadata,
    sa.Column(
        'sid',
        sa.Integer,
        sa.ForeignKey(symbol_price.c.sid),
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column('trade_dt', sa.String(10),nullable=False),
    sa.Column('mkv', sa.Numeric(15,5),nullable=False),
    sa.Column('mkv_cap', sa.Numeric(15,5),nullable=False),
    sa.Column('mkv_strict', sa.Numeric(15,5), nullable=False),
)
# default = 0

symbol_massive = sa.Table(
    'symbol_massive',
    metadata,
    sa.Column(
        'sid',
        sa.Integer,
        sa.ForeignKey(symbol_price.c.sid),
        nullable=False,
        primary_key=True,
    ),
    sa.Column('股东', sa.Text),
    sa.Column('途径', sa.String(20)),
    sa.Column('方式', sa.String(20)),
    sa.Column('变动股本',sa.Numeric(10,5), nullable=False),
    sa.Column('占总流通比例', sa.Numeric(10,5), nullable=False),
    sa.Column('总持仓', sa.Numeric(10,5), nullable=False),
    sa.Column('占总股本比例', sa.Numeric(10,5), nullable=False),
    sa.Column('总流通股', sa.Numeric(10,5), nullable=False),
    sa.Column('变动开始日', sa.String(10)),
    sa.Column('变动截止日', sa.String(10)),
    sa.Column('公告日', sa.String(10)),
)

symbol_delist = sa.Table(
    'symbol_delist',
    metadata,
    sa.Column(
        'sid',
        sa.String(10),
        sa.ForeignKey(symbol_price.c.sid),
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column('delist_date', sa.String(10)),
    sa.Column('cname', sa.String(20)),
)

trading_calendar = sa.Table(
    'trading_calendar',
    metadata,
    sa.Column(
        'trading_day',
        sa.Text,
        unique=True,
        nullable=False,
        primary_key=True,
        index = True,
    ),
)

market_marign = sa.Table(
    'market_marign',
    metadata,
    sa.Column(
        'trade_dt',
        sa.String(10),
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column('融资余额', sa.String(20)),
    sa.Column('融券余额', sa.String(20)),
    sa.Column('融资融券总额', sa.String(20)),
    sa.Column('融资融券差额', sa.String(20)),
)

version_info = sa.Table(
    'version_info',
    metadata,
    sa.Column(
        'id',
        sa.Integer,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        'version',
        sa.Integer,
        unique=True,
        nullable=False,
    ),
    # This constraint ensures a single entry in this table
    sa.CheckConstraint('id <= 1'),
)
