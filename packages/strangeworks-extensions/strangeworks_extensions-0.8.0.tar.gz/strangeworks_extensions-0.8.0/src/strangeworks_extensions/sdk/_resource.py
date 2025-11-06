"""resources.py."""

from strangeworks_core.errors.error import StrangeworksError
from strangeworks_core.platform.gql import Operation
from strangeworks_core.types.resource import Resource

from strangeworks_extensions.sdk._gql import SDKAPI

_get_op = Operation(
    query="""
query sdk_get_resources($product_slugs: [String!], $first: Int, $after: ID) {
  workspace {
    resources(
      productSlugs: $product_slugs
      pagination: {after: $after, first: $first}
    ) {
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        cursor
        node {
          slug
          product {
            slug
          }
          configurations {
            key
            type
            valueJson
          }
          status
        }
      }
    }
  }
}
    """
)


def get(
    client: SDKAPI,
    resource_slug: str | None = None,
    product_slug: str | None = None,
    batch_size: int = 50,
) -> list[Resource]:
    """Retrieve a list of available resources.

    Parameters
    ----------
    client: StrangeworksGQLClient
        client to access the sdk api on the platform.
    resource_slug: Optional[str]
        If supplied, only the resource whose slug matches will be returned. Defaults to
        None.
    batch_size: int
        Number of jobs to retrieve with each request. Defaults to 50.

    Return
    ------
    Optional[List[Resource]]
        List of resources or None if workspace has no resources configured.
    """
    hasNextPage: bool = True
    resources: list[Resource] = []
    cursor: str | None = None

    while hasNextPage:
        resource_list, cursor, hasNextPage = _retrieve_resources(
            client=client,
            product_slug=product_slug,
            batch_size=batch_size,
            cursor=cursor,
        )

        if resource_list:
            if resource_slug:
                edges = resource_list.get("edges", [])
                for x in edges:
                    node = x.get("node")
                    if node and node.get("slug") == resource_slug:
                        # we found what we are looking for
                        resources.append(Resource.from_dict(node))
                        hasNextPage = False
                        break
            else:
                # no resource_slug provided, return everything.
                _tmp: list[Resource] = [
                    Resource.from_dict(node)
                    for x in resource_list.get("edges", [])
                    if (node := x.get("node")) is not None
                ]
                resources.extend(_tmp)

    return resources


def _retrieve_resources(
    client: SDKAPI,
    product_slug: str | None = None,
    batch_size: int = 50,
    cursor: str | None = None,
) -> tuple[dict, str | None, bool]:
    workspace = client.execute(
        op=_get_op,
        product_slugs=[product_slug],
        first=batch_size,
        after=cursor,
    ).get("workspace")

    if not workspace:
        raise StrangeworksError(
            message="unable to retrieve resources (no workspace returned)"
        )

    resource = workspace.get("resources")
    if not resource:
        return {}, "", False

    page_info = resource .get("pageInfo")
    cursor = page_info.get("endCursor")
    hasNextPage = page_info.get("hasNextPage")

    return workspace.get("resources"), cursor, hasNextPage
