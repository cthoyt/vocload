# Name: GONode.py
# Purpose: representation of a node in the Gene Ontology

import Node

class GONode(Node.Node):
    """
    #  Object representing a node in the GO vocabulary
    """

    def __init__(self, id, label):
        """
        #  Requires:
        #    id: string
        #    label: string
        #  Effects:
        #    constructor (adds definition attribute)
        #  Modifies:
        #    self.definition
        #  Returns:
        #  Exceptions:
        """

        Node.Node.__init__(self, id, label)
        self.definition = ''
        return

    def setDefinition(self, definition):
        """
        #  Requires:
        #    definition: string
        #  Effects:
        #    Sets the GO term's definition to the given string
        #  Modifies:
        #    self.definition (attribute specific to GONode)
        #  Returns:
        #  Exceptions:
        """

        self.definition = definition

    def getDefinition(self):
        """
        #  Requires:
        #  Effects:
        #    Returns the GO term's definition
        #  Modifies:
        #  Returns:
        #    self.definition: string
        #  Exceptions:
        """

        return self.definition

#
# Warranty Disclaimer and Copyright Notice
# 
#  THE JACKSON LABORATORY MAKES NO REPRESENTATION ABOUT THE SUITABILITY OR 
#  ACCURACY OF THIS SOFTWARE OR DATA FOR ANY PURPOSE, AND MAKES NO WARRANTIES, 
#  EITHER EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR A 
#  PARTICULAR PURPOSE OR THAT THE USE OF THIS SOFTWARE OR DATA WILL NOT 
#  INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS, OR OTHER RIGHTS.  
#  THE SOFTWARE AND DATA ARE PROVIDED "AS IS".
# 
#  This software and data are provided to enhance knowledge and encourage 
#  progress in the scientific community and are to be used only for research 
#  and educational purposes.  Any reproduction or use for commercial purpose 
#  is prohibited without the prior express written permission of the Jackson 
#  Laboratory.
# 
# Copyright � 1996, 1999, 2000 by The Jackson Laboratory
# All Rights Reserved
#
