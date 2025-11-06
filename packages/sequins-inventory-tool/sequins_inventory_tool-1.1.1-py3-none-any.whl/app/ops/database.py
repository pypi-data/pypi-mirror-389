"""CLI to manipulate the database directly."""

import logging

import pymongo
from pymongo import ASCENDING, IndexModel
import typer
from typing_extensions import Annotated

from app.console import console
from app.ops.database_user import app as database_user_app

logger = logging.getLogger(__name__)

app = typer.Typer()
app.add_typer(database_user_app, name='user')

BLEND_COLLECTION_NAME = 'blends'
SEQUIN_COLLECTION_NAME = 'sequins'
VARIANT_COLLECTION_NAME = 'variants'
GROUP_COLLECTION_NAME = 'groups'
LOCATION_COLLECTION_NAME = 'locations'
PART_DEFINITIONS_COLLECTION_NAME = 'part_definitions'
PART_COLLECTION_NAME = 'parts'
TILE_COLLECTION_NAME = 'tiles'
POOL_COLLECTION_NAME = 'pools'
USER_COLLECTION_NAME = 'users'

INDEXES = {
    SEQUIN_COLLECTION_NAME: [
        {'keys': [('id', ASCENDING)], 'unique': True},
        {'keys': [('sequence', ASCENDING)], 'unique': True},
    ],
    VARIANT_COLLECTION_NAME: [
        {
            'keys': [
                ('chrom', ASCENDING),
                ('pos', ASCENDING),
                ('ref', ASCENDING),
                ('alt', ASCENDING),
            ],
            'unique': True,
        }
    ],
    GROUP_COLLECTION_NAME: [
        {'keys': [('id', ASCENDING)], 'unique': True},
        {'keys': [('sequin_ids_hash', ASCENDING)], 'unique': True},
    ],
    BLEND_COLLECTION_NAME: [{'keys': [('id', ASCENDING)], 'unique': True}],
    PART_DEFINITIONS_COLLECTION_NAME: [
        {
            'keys': [('part_number', ASCENDING)],
            'unique': True,
        },
    ],
    PART_COLLECTION_NAME: [
        {
            'keys': [('part_number', ASCENDING)],
            'unique': False,
        },
        {
            'keys': [
                ('part_number', ASCENDING),
                ('constituent_lots_hash', ASCENDING),
            ],
            'unique': True,
        },
        {'keys': [('location', ASCENDING)], 'unique': False},
        {'keys': [('status', ASCENDING)], 'unique': False},
        {
            'keys': [('status', ASCENDING), ('quote_reference', ASCENDING)],
            'unique': False,
        },
        {'keys': [('created_at_utc', ASCENDING)], 'unique': False},
    ],
    TILE_COLLECTION_NAME: [
        {'keys': [('id', ASCENDING)], 'unique': True},
        {'keys': [('sequence', ASCENDING)], 'unique': False},
    ],
    POOL_COLLECTION_NAME: [{'keys': [('id', ASCENDING)], 'unique': True}],
    USER_COLLECTION_NAME: [
        {'keys': [('username', ASCENDING)], 'unique': True},
        {'keys': [('api_key_hash', ASCENDING)], 'unique': False},
    ],
    LOCATION_COLLECTION_NAME: [
        {'keys': [('name', ASCENDING)], 'unique': False},
        {'keys': [('parent_key', ASCENDING)], 'unique': False},
    ],
}


@app.command(name='create-indexes')
def create_indexes(ctx: typer.Context):
    server = ctx.obj['database_server_name']
    database = ctx.obj['database_name']

    logger.debug('server = %s, database = %s', server, database)

    console.log(f'Creating indexes for database {database}.')

    client = pymongo.MongoClient(server)
    db = client[database]

    for collection_name, indexes in INDEXES.items():
        index_models = [
            # pyrefly: ignore  # bad-argument-type
            IndexModel(index['keys'], unique=index['unique'])
            for index in indexes
        ]
        db[collection_name].create_indexes(index_models)

    console.log('Indexes created successfully.')


@app.command(name='sync-indexes')
def sync_indexes(ctx: typer.Context):
    server = ctx.obj['database_server_name']
    database = ctx.obj['database_name']

    logger.debug('server = %s, database = %s', server, database)

    console.log(f'Syncing indexes for database {database}.')

    client = pymongo.MongoClient(server)
    db = client[database]

    # Create existing indexes if they do not already exist.
    for collection_name, indexes in INDEXES.items():
        existing_indexes_cursor = db[collection_name].list_indexes()
        existing_indexes = {
            index['name']: index for index in existing_indexes_cursor
        }

        index_models = []
        for index in indexes:
            # pyrefly: ignore  # bad-argument-type
            index_model = IndexModel(index['keys'], unique=index['unique'])
            index_name = index_model.document['name']

            if index_name not in existing_indexes:
                index_models.append(index_model)
            else:
                # Check if the 'unique' property is different
                existing_index = existing_indexes[index_name]
                if existing_index.get('unique', False) != index['unique']:
                    # Drop the old index and create the new one
                    db[collection_name].drop_index(index_name)
                    index_models.append(index_model)

        if index_models:
            db[collection_name].create_indexes(index_models)

    # Drop indexes that are not in our defined set.
    for collection_name, indexes in INDEXES.items():
        defined_index_names = {
            # pyrefly: ignore  # bad-argument-type
            IndexModel(index['keys'], unique=index['unique']).document['name']
            for index in indexes
        }

        existing_indexes = db[collection_name].list_indexes()
        extra_indexes = []
        # pyrefly: ignore  # bad-assignment
        for index in existing_indexes:
            if (
                index['name'] not in defined_index_names
                and index['name'] != '_id_'
            ):
                extra_indexes.append(index['name'])

        if extra_indexes:
            for index_name in extra_indexes:
                db[collection_name].drop_index(index_name)

    console.log('Indexes synced successfully.')


@app.command(name='drop')
def drop_database(ctx: typer.Context):
    server = ctx.obj['database_server_name']
    database = ctx.obj['database_name']

    logger.debug('server = %s, database = %s', server, database)

    client = pymongo.MongoClient(server)
    client.drop_database(database)

    console.log('Database dropped successfully.')


@app.command(name='delete-documents')
def delete_documents(
    ctx: typer.Context,
    name: Annotated[
        str, typer.Argument(help='The collection to delete all documents from.')
    ],
    force: Annotated[
        bool,
        typer.Option('--force', help='Force deletion without confirmation.'),
    ] = False,
):
    if not force:
        confirm = typer.confirm(
            'Are you sure you want to delete all documents from the '
            f'collection: {name}?'
        )
        if not confirm:
            console.print('Deletion cancelled.')
            raise typer.Exit()

    server = ctx.obj['database_server_name']
    database = ctx.obj['database_name']

    client = pymongo.MongoClient(server)
    collection = client[database][name]

    result = collection.delete_many({})

    console.log(f'Deleted {result.deleted_count} documents from {name}.')


@app.command(name='mirror')
def mirror_database(
    ctx: typer.Context,
    source_database: Annotated[
        str, typer.Option('--source-db', help='Source database name.')
    ],
    target_database: Annotated[
        str, typer.Option('--target-db', help='Target database name.')
    ],
    force: Annotated[
        bool,
        typer.Option('--force', help='Force mirroring without confirmation.'),
    ] = False,
):
    """Mirror all contents from source database to target database.

    This replaces all data in the target database with an exact copy of the
    source database. Collections not in source will be dropped from target.
    Assumes source and target are on the same MongoDB server.
    """
    server = ctx.obj['database_server_name']

    if not force:
        confirm = typer.confirm(
            f'Are you sure you want to mirror {source_database} to '
            f'{target_database} on {server}? '
            'This will replace all data in the target database.'
        )
        if not confirm:
            console.print('Mirroring cancelled.')
            raise typer.Exit()

    if target_database == 'production':
        confirm = typer.confirm(
            f'The target for the mirror is {target_database} on {server}. '
            'This will replace all data in the target database. '
            'Are you REALLY sure you want to continue?'
        )
        if not confirm:
            console.print(f'Mirroring to {target_database} cancelled.')
            raise typer.Exit()

    logger.debug(
        'Mirroring from %s to %s on %s',
        source_database,
        target_database,
        server,
    )

    client = pymongo.MongoClient(server)
    source_db = client[source_database]
    target_db = client[target_database]

    # Get list of collections in source
    source_collections = source_db.list_collection_names()

    # Drop all collections in target that are not in source
    target_collections = set(target_db.list_collection_names())
    source_collections_set = set(source_collections)
    to_drop = target_collections - source_collections_set
    for coll_name in to_drop:
        target_db.drop_collection(coll_name)
        console.log(f'Dropped collection {coll_name} from target.')

    # Copy each collection from source to target
    for coll_name in source_collections:
        source_coll = source_db[coll_name]
        target_coll = target_db[coll_name]

        # Clear target collection
        target_coll.delete_many({})

        # Copy documents
        documents = list(source_coll.find({}))
        if documents:
            target_coll.insert_many(documents)
            console.log(f'Copied {len(documents)} documents to {coll_name}.')
        else:
            console.log(f'Collection {coll_name} is empty.')

    console.log('Database mirroring completed successfully.')
