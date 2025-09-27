package gov.nysenate.openleg.processors.law;

import gov.nysenate.openleg.legislation.law.LawDocumentType;
import gov.nysenate.openleg.legislation.law.LawTree;
import gov.nysenate.openleg.legislation.law.LawTreeNode;
import gov.nysenate.openleg.legislation.law.LawVersionId;
import org.apache.commons.lang3.StringUtils;

import java.util.Stack;
import java.util.regex.Matcher;

/**
 * Constructs document hierarchies using document id prefixes.
 */
public class IdBasedLawBuilder extends AbstractLawBuilder implements LawBuilder {
    /** Stack of the current parent nodes, used to determine hierarchy. */
    protected Stack<LawTreeNode> parentNodes = new Stack<>();

    public IdBasedLawBuilder(LawVersionId lawVersionId, LawTree previousTree) {
        super(lawVersionId, previousTree);
    }

    /**
     * We determine the position of a node based on whether any of the nodes in the parent stack has a location id
     * that prefixes the current document's location id. The specific location id (the matched prefix from the parent
     * document removed) is returned.
     *
     * For example given the locationId 'A2P1SP3', we will pop the parent stack until we find its parent 'A2P1'
     * or reach the root node. The new portion 'SP3' would be the returned value which serves as the docTypeId.
     *
     * @param docId String
     * @return String
     */
    @Override
    protected String determineHierarchy(String docId) {
        if (docId.startsWith(CITY_TAX_STR + "P"))
            return docId.replace(CITY_TAX_STR, "");
        String blockLocID = docId.substring(3);
        while (!currParent().isRootNode()) {
            String parentLocID = currParent().getLocationId();
            if (StringUtils.startsWith(blockLocID, parentLocID)) {
                // Remove parent location ID.
                String trimLocId = StringUtils.removeStart(blockLocID, parentLocID);
                LawDocumentType parentType = currParent().getDocType();
                Matcher blockMatch = LOCATION_PATTERN.matcher(trimLocId);
                if (blockMatch.matches() && lawLevelCodes.get(blockMatch.group(1)) != parentType)
                    return trimLocId;
            }
            parentNodes.pop();
        }
        return blockLocID;
    }

    @Override
    protected void addChildNode(LawTreeNode node) {
        // Handles special GCT sections.
        if (node.getDocumentId().matches(CITY_TAX_STR.substring(0, 6) + "(B|AP[^1].*)")) {
            parentNodes.pop();
            if (node.getLocationId().endsWith("B"))
                parentNodes.pop();
        }
        if (currParent() != null)
            currParent().addChild(node);
        // Section nodes should never become parents because they are the most granular (at the moment).
        if (!node.getDocType().isSection())
            parentNodes.push(node);
    }

    @Override
    protected boolean isNodeListEmpty() {
        return parentNodes.empty();
    }

    @Override
    protected void clearParents() {
        parentNodes.clear();
    }

    /**
     * Peek at the parent node stack which holds the current parent.
    */
    protected LawTreeNode currParent() {
        return parentNodes.empty() ? null : parentNodes.peek();
    }
}
