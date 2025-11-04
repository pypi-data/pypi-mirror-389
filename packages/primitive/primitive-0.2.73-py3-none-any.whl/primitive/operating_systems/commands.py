import click
import typing
from loguru import logger

if typing.TYPE_CHECKING:
    from ..client import Primitive


@click.group("operating-systems")
@click.pass_context
def cli(context):
    "Operating Systems"
    pass


@cli.command("list")
@click.option(
    "--organization-slug",
    help="Organization slug to list operating systems for",
    required=False,
)
@click.pass_context
def operating_systems_list_command(context, organization_slug):
    primitive: Primitive = context.obj.get("PRIMITIVE")

    organization = (
        primitive.organizations.get_organization(slug=organization_slug)
        if organization_slug
        else primitive.organizations.get_default_organization()
    )

    if not organization:
        if organization_slug:
            logger.error(f"No organization found with slug {organization_slug}")
        else:
            logger.error("Failed to fetch default organization")

    operating_systems = primitive.operating_systems.list(
        organization_id=organization["id"]
    )
    operating_system_slugs = [
        operating_system["slug"] for operating_system in operating_systems
    ]

    newline = "\n"
    logger.info(
        f"Operating systems: {newline}- {f'{newline}- '.join(operating_system_slugs)}"
    )


@cli.command("create")
@click.option("--slug", help="Slug for created operating system", required=True)
@click.option(
    "--iso-file", help="Path to operating system iso file to upload", required=True
)
@click.option(
    "--checksum-file",
    help="Path to operating system checksum file to upload",
    required=True,
)
@click.option(
    "--checksum-file-type", help="The type of the checksum file", required=True
)
@click.option(
    "--organization-slug",
    help="Organization to create the operating system in",
    required=False,
)
@click.option(
    "--is-global",
    help="[ADMIN] Create global operating system",
    is_flag=True,
    hidden=True,
)
@click.pass_context
def create_command(
    context,
    slug,
    iso_file,
    checksum_file,
    checksum_file_type,
    organization_slug,
    is_global,
):
    primitive: Primitive = context.obj.get("PRIMITIVE")

    if organization_slug:
        organization = primitive.organizations.get_organization(slug=organization_slug)
    elif is_global:
        organization = primitive.organizations.get_organization(slug="primitive")
    else:
        organization = primitive.organizations.get_default_organization()

    if not organization:
        if organization_slug:
            logger.error(f"No organization found with slug {organization_slug}")
            return
        elif is_global:
            logger.error("Failed to fetch primitive organization")
            return
        else:
            logger.error("Failed to fetch default organization")
            return

    try:
        primitive.operating_systems.create(
            slug=slug,
            iso_file=iso_file,
            checksum_file=checksum_file,
            checksum_file_type=checksum_file_type,
            organization_id=organization["id"],
            is_global=is_global,
        )
    except Exception as error:
        logger.error(error)
        return

    logger.success("Operating system created in primitive.")


@cli.command("download")
@click.option("--id", help="Operating system ID", required=False)
@click.option("--slug", help="Operating system slug", required=False)
@click.option("--organization-slug", help="Organization slug", required=False)
@click.option(
    "--directory",
    help="Directory to download the operating system files to",
    required=False,
)
@click.pass_context
def download(context, id, slug, organization_slug, directory):
    if not (id or slug):
        raise click.UsageError("You must provide either --id or --slug.")
    if id and slug:
        raise click.UsageError("You can only specify one of --id or --slug.")

    primitive: Primitive = context.obj.get("PRIMITIVE")

    organization = (
        primitive.organizations.get_organization(slug=organization_slug)
        if organization_slug
        else primitive.organizations.get_default_organization()
    )

    if not organization:
        if organization_slug:
            logger.error(f"No organization found with slug {organization_slug}")
            return
        else:
            logger.error("Failed to fetch default organization")
            return

    try:
        operating_system_directory = primitive.operating_systems.download(
            id=id, slug=slug, organization_id=organization["id"], directory=directory
        )
    except Exception as error:
        logger.error(error)
        return

    logger.success(
        f"Successfully downloaded operating system to {operating_system_directory}"
    )


@cli.group("remotes")
@click.pass_context
def remotes(context):
    "Remotes"
    pass


@remotes.command("download")
@click.pass_context
@click.argument("operating-system")
@click.option(
    "--directory",
    help="Directory to download the operating system files to",
    required=False,
)
def operating_system_remotes_download_command(
    context, operating_system, directory=None
):
    primitive: Primitive = context.obj.get("PRIMITIVE")

    try:
        primitive.operating_systems.download_remote(
            remote_operating_system_name=operating_system, directory=directory
        )
    except Exception as error:
        logger.error(error)
        return

    logger.success(f"Successfully downloaded operating system files to {directory}")


@remotes.command("mirror")
@click.pass_context
@click.argument("operating-system")
@click.option("--slug", help="Slug of the operating system", required=False)
@click.option(
    "--organization-slug",
    help="Slug of the organization to upload the operating system to",
    required=False,
)
@click.option(
    "--directory",
    help="Directory to download the operating system files to",
    required=False,
)
@click.option(
    "--is-global",
    help="[ADMIN] Create global operating system",
    is_flag=True,
    hidden=True,
)
def operating_system_mirror_command(
    context,
    operating_system,
    slug=None,
    organization_slug=None,
    directory=None,
    is_global=False,
):
    primitive: Primitive = context.obj.get("PRIMITIVE")

    if organization_slug:
        organization = primitive.organizations.get_organization(slug=organization_slug)
    elif is_global:
        organization = primitive.organizations.get_organization(slug="primitive")
    else:
        organization = primitive.organizations.get_default_organization()

    if not organization:
        if organization_slug:
            logger.error(f"No organization found with slug {organization_slug}")
            return
        elif is_global:
            logger.error("Failed to fetch primitive organization")
            return
        else:
            logger.error("Failed to fetch default organization")
            return

    try:
        iso_file_path, checksum_file_path = primitive.operating_systems.download_remote(
            operating_system, directory=directory
        )

        checksum_file_type = primitive.operating_systems.get_remote_info(
            operating_system
        )["checksum_file_type"]

        primitive.operating_systems.create(
            slug=slug if slug else operating_system,
            iso_file=iso_file_path,
            checksum_file=checksum_file_path,
            checksum_file_type=checksum_file_type.value,
            organization_id=organization["id"],
            is_global=is_global,
        )
    except Exception as error:
        logger.error(error)
        return

    logger.success("Successfully mirrored operating system")


@remotes.command("list")
@click.pass_context
def remote_operating_systems_list_command(context):
    primitive: Primitive = context.obj.get("PRIMITIVE")
    remotes_list = primitive.operating_systems.list_remotes()
    remote_slugs = [remote["slug"] for remote in remotes_list]
    newline = "\n"
    logger.info(
        f"Remote operating systems: {newline}- {f'{newline}- '.join(remote_slugs)}"
    )
